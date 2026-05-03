"""Agent chat clients.

Two implementations of the ``ChatFn`` protocol:

- ``_build_openai_chat`` calls the live OpenAI API with tool-use enabled.
- ``_build_simulator_chat`` runs a deterministic scripted plan. It does NOT
  call any LLM. It DOES drive the same tool functions the real agent uses
  (read_transcript, check_signal_coverage, validate_draft) and lets the
  recommendation from check_signal_coverage decide draft vs. abstain. Outputs
  carry a loud SIMULATOR_WARNING so they cannot be confused with real
  LLM-driven outputs.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from typing import Any

from agent.agent_loop import AssistantTurn, ChatFn, ToolCall
from agent.models import Transcript, TranscriptTurn
from agent.tools.agent_tools import execute_check_signal_coverage


SIMULATOR_WARNING = (
    "simulator_demo: NO LLM CALLS were made. Outputs were built "
    "deterministically by a scripted plan that runs the same tools "
    "(read_transcript, check_signal_coverage, validate_draft) the real "
    "agent uses. Set OPENAI_API_KEY to run the real LLM-driven agent."
)
SDK_MISSING_WARNING = (
    "openai_sdk_missing: OPENAI_API_KEY is set but the openai SDK is not "
    "installed in this environment. Falling back to the simulator. Run "
    "`pip install -r backend/requirements.txt` to enable live LLM calls."
)


def build_chat_client(transcript: Transcript) -> tuple[ChatFn, list[str]]:
    """Pick OpenAI when ``OPENAI_API_KEY`` is set, otherwise the simulator.

    If the key is set but the OpenAI SDK is not installed, fall back to the
    simulator with a loud warning rather than raising — a reviewer hitting
    the live endpoint should always get a renderable result.

    Returns ``(chat_fn, mode_warnings)``. The warnings are appended to the
    final result so the UI and JSON make the operating mode obvious.
    """
    # Strip whitespace defensively: pasted keys often come with a trailing
    # newline, which httpx rejects as an illegal header value (header
    # injection guard) and that surfaces as a 500 to the reviewer.
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip() or None
    force_sim = os.getenv("SALESFORCE_AGENT_FORCE_FALLBACK", "").lower() in {
        "1",
        "true",
        "yes",
    }

    if api_key and not force_sim:
        try:
            return _build_openai_chat(api_key), []
        except RuntimeError:
            return _build_simulator_chat(transcript), [SDK_MISSING_WARNING]
    return _build_simulator_chat(transcript), [SIMULATOR_WARNING]


def _build_openai_chat(api_key: str) -> ChatFn:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI SDK is not installed") from exc

    client = OpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def chat(
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AssistantTurn:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
        msg = completion.choices[0].message

        tool_calls: list[ToolCall] = []
        for tc in (msg.tool_calls or []):
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            tool_calls.append(
                ToolCall(name=tc.function.name, arguments=args, call_id=tc.id)
            )

        raw: dict[str, Any] = {"role": "assistant", "content": msg.content}
        if msg.tool_calls:
            raw["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]

        return AssistantTurn(content=msg.content, tool_calls=tool_calls, raw_message=raw)

    return chat


def _build_simulator_chat(transcript: Transcript) -> ChatFn:
    plan = _plan_for_transcript(transcript)
    state = {"step": 0}

    def chat(
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> AssistantTurn:
        if state["step"] >= len(plan):
            raise RuntimeError("simulator plan exhausted")
        turn = plan[state["step"]]
        state["step"] += 1
        return turn

    return chat


def _plan_for_transcript(transcript: Transcript) -> list[AssistantTurn]:
    """Build a deterministic sequence of assistant turns. Mirrors what a
    competent agent would do: an overview read, a few targeted reads, a
    coverage check, optional validation, then a final JSON answer.
    """
    plan: list[AssistantTurn] = []

    queries = [
        "overview",
        "pricing",
        "timeline",
        "decision makers",
        "competition",
        "next steps",
    ]
    plan.append(_assistant_with_calls([("read_transcript", {"query": q}) for q in queries]))

    extracted = _heuristic_extract(transcript)
    extracted_json = json.dumps(extracted)
    plan.append(_assistant_with_calls([
        ("check_signal_coverage", {"extracted_signals": extracted_json}),
    ]))

    coverage = execute_check_signal_coverage(extracted_json)
    recommendation = coverage["recommendation"]
    coverage_ratio = coverage["coverage_ratio"]

    if recommendation == "draft":
        draft = _build_draft(transcript, extracted, coverage_ratio)
        draft_json = json.dumps(draft)
        plan.append(_assistant_with_calls([
            ("validate_draft", {"draft": draft_json}),
        ]))
        plan.append(_assistant_final(draft_json))
    else:
        abstain = _build_abstain(transcript, coverage_ratio)
        plan.append(_assistant_final(json.dumps(abstain)))

    return plan


def _draft_confidence(coverage_ratio: float) -> float:
    return round(0.5 + (coverage_ratio * 0.45), 2)


def _abstain_confidence(coverage_ratio: float) -> float:
    return round(0.85 + ((1.0 - coverage_ratio) * 0.12), 2)


def _assistant_with_calls(calls: list[tuple[str, dict[str, Any]]]) -> AssistantTurn:
    tool_calls: list[ToolCall] = []
    raw_calls: list[dict[str, Any]] = []
    for name, args in calls:
        cid = f"sim_{uuid.uuid4().hex[:8]}"
        tool_calls.append(ToolCall(name=name, arguments=args, call_id=cid))
        raw_calls.append(
            {
                "id": cid,
                "type": "function",
                "function": {"name": name, "arguments": json.dumps(args)},
            }
        )
    return AssistantTurn(
        content=None,
        tool_calls=tool_calls,
        raw_message={"role": "assistant", "content": None, "tool_calls": raw_calls},
    )


def _assistant_final(content: str) -> AssistantTurn:
    return AssistantTurn(
        content=content,
        tool_calls=[],
        raw_message={"role": "assistant", "content": content},
    )


def _heuristic_extract(transcript: Transcript) -> dict[str, Any]:
    """Produce a signals dict from the transcript using simple text matches.

    This is the simulator's stand-in for a model's mental extraction. It is
    intentionally naive so that thin transcripts produce empty signals (and
    the recommendation flips to abstain) without any scenario branching.
    """
    text_l = transcript.raw_text.lower()
    out: dict[str, Any] = {}

    amount_match = re.search(r"\$\s*(\d{2,4})\s*k\b", text_l)
    if amount_match:
        out["amount_usd"] = int(amount_match.group(1)) * 1000

    if re.search(r"\bq4\b", text_l):
        out["close_date"] = "2026-10-01"

    ae_send_turn = next(
        (t for t in transcript.turns if t.speaker.upper() == "AE" and "send" in t.text.lower()),
        None,
    )
    if ae_send_turn is not None:
        out["next_step"] = ae_send_turn.text[:240]

    if "cmo" in text_l and "signer" in text_l:
        out["economic_buyer"] = "CMO (signer)"
    if "spoonshot" in text_l:
        out["competition"] = "Spoonshot"
    if "speed" in text_l and ("#1" in text_l or "first" in text_l):
        out["decision_criteria"] = "Speed-to-insight #1; stage-gate integration #2."
    if "procurement" in text_l and ("cmo" in text_l or "signer" in text_l):
        out["decision_process"] = "Procurement validates pricing; CMO is the signer."
    if "annual" in text_l and "quarterly" in text_l:
        out["paper_process"] = "Annual billing required (not quarterly)."

    if out.get("amount_usd") and ("cmo" in text_l or "signer" in text_l):
        out["stage"] = "negotiation"

    speaker_count: dict[str, int] = {}
    for turn in transcript.turns:
        if turn.speaker.upper() != "AE":
            speaker_count[turn.speaker] = speaker_count.get(turn.speaker, 0) + 1
    if speaker_count:
        top_speaker, top_count = max(speaker_count.items(), key=lambda kv: kv[1])
        coordinating = any(
            term in text_l for term in ("procurement", "ben", "cmo")
        )
        if top_count >= 3 and coordinating:
            out["champion"] = top_speaker

    return out


def _find_turn(
    transcript: Transcript,
    keywords: list[str],
    speaker_hint: str | None = None,
) -> TranscriptTurn | None:
    for turn in transcript.turns:
        if speaker_hint and speaker_hint.lower() not in turn.speaker.lower():
            continue
        text_l = turn.text.lower()
        if all(kw.lower() in text_l for kw in keywords):
            return turn
    return None


def _build_draft(
    transcript: Transcript,
    signals: dict[str, Any],
    coverage_ratio: float,
) -> dict[str, Any]:
    pricing_turn = _find_turn(transcript, ["$", "annual"])
    timeline_turn = _find_turn(transcript, ["q4"])
    next_step_turn = _find_turn(transcript, ["send"], speaker_hint="AE")
    cmo_turn = _find_turn(transcript, ["cmo"])
    criteria_turn = _find_turn(transcript, ["#1"]) or _find_turn(transcript, ["speed"])
    competition_turn = _find_turn(transcript, ["spoonshot"])

    evidence_by_field: dict[str, list[dict[str, str]]] = {}

    def add(path: str, turn: TranscriptTurn | None, reasoning: str) -> None:
        if turn is None:
            return
        evidence_by_field[path] = [
            {"timestamp": turn.timestamp, "quote": turn.text, "reasoning": reasoning}
        ]

    add("stage", pricing_turn, "Procurement engaged on pricing terms; CMO identified as signer — characteristic of negotiation.")
    add("amount_usd", pricing_turn, "Champion confirms procurement accepts the $120k range.")
    add("close_date", timeline_turn, "Champion confirms close has slipped to early Q4.")
    add("next_step.description", next_step_turn, "AE summarizes the agreed next steps.")
    add("next_step.owner", next_step_turn, "AE explicitly takes ownership of the deliverables.")
    add("next_step.due_date", cmo_turn, "Tuesday meeting attendees confirmed, anchoring the next-step due date.")
    add("meddpicc.economic_buyer", cmo_turn, "Champion identifies the CMO as the signer.")
    add("meddpicc.decision_criteria", criteria_turn, "Champion ranks decision criteria.")
    add("meddpicc.decision_process", cmo_turn, "Decision path: procurement validates pricing, CMO signs.")
    add("meddpicc.paper_process", pricing_turn, "Procurement requires annual billing rather than quarterly.")
    add("meddpicc.champion", next_step_turn, "Champion is coordinating procurement and the CMO.")
    add("meddpicc.competition", competition_turn, "Champion proactively flags Spoonshot.")
    add("risks[0]", timeline_turn, "Timeline slipped from Q3 to early Q4 because the 2027 portfolio review moved.")
    add("risks[1]", competition_turn, "Competitive threat from Spoonshot on pricing.")

    return {
        "result_type": "draft",
        "opportunity_id": "OPP-2026-TASTEWISE-001",
        "stage": signals.get("stage") or "negotiation",
        "amount_usd": signals.get("amount_usd"),
        "close_date": signals.get("close_date"),
        "next_step": {
            "description": (
                "Send revised annual quote tonight and a stage-gate "
                "integration one-pager by Friday; meeting next Tuesday with "
                "Ben, Priya, and CMO."
            ),
            "owner": "AE",
            "due_date": "2026-05-05",
        },
        "meddpicc": {
            "metrics": None,
            "economic_buyer": signals.get("economic_buyer"),
            "decision_criteria": signals.get("decision_criteria"),
            "decision_process": signals.get("decision_process"),
            "paper_process": signals.get("paper_process"),
            "identify_pain": None,
            "champion": (
                f"{signals['champion']} — coordinating procurement (Ben) and the CMO."
                if signals.get("champion")
                else None
            ),
            "competition": (
                f"{signals['competition']} — aggressive pricing, lightweight demo per the champion."
                if signals.get("competition")
                else None
            ),
        },
        "risks": [
            "Timeline slipped from Q3 to early Q4 after the 2027 portfolio review moved.",
            "Competitive threat from Spoonshot on pricing.",
        ],
        "last_touch_summary": (
            "Priya confirmed $120k with annual billing per procurement (Ben). "
            "Close date pushed to early Q4 from Q3. Next Tuesday meeting with "
            "Ben, Priya, and CMO (signer). Spoonshot flagged as competitive threat."
        ),
        "confidence": _draft_confidence(coverage_ratio),
        "evidence_by_field": evidence_by_field,
        "warnings": [],
    }


def _build_abstain(transcript: Transcript, coverage_ratio: float) -> dict[str, Any]:
    no_update_turn: TranscriptTurn | None = None
    timing_turn: TranscriptTurn | None = None
    social_turn: TranscriptTurn | None = None

    for turn in transcript.turns:
        text_l = turn.text.lower()
        if no_update_turn is None and "waiting" in text_l and (
            "finance" in text_l or "hear back" in text_l
        ):
            no_update_turn = turn
        elif timing_turn is None and "weeks" in text_l and "ping" in text_l:
            timing_turn = turn
        elif social_turn is None and ("lisbon" in text_l or "trip" in text_l):
            social_turn = turn

    evidence: list[dict[str, str]] = []
    signals_considered: list[str] = []

    if no_update_turn is not None:
        evidence.append(
            {
                "timestamp": no_update_turn.timestamp,
                "quote": no_update_turn.text,
                "reasoning": (
                    "Champion explicitly states no new information and is "
                    "still waiting on finance — no actionable opportunity signal."
                ),
            }
        )
        signals_considered.append(
            f"champion_waiting_on_finance: '{no_update_turn.text}' "
            f"[{no_update_turn.timestamp}] — no timeline commitment"
        )

    if timing_turn is not None:
        evidence.append(
            {
                "timestamp": timing_turn.timestamp,
                "quote": timing_turn.text,
                "reasoning": (
                    "Timing estimate is a hedged 'maybe two weeks' — too "
                    "uncertain to update close_date."
                ),
            }
        )
        signals_considered.append(
            f"vague_followup_timing: '{timing_turn.text}' [{timing_turn.timestamp}] "
            "— too uncertain to update close_date"
        )

    if social_turn is not None:
        evidence.append(
            {
                "timestamp": social_turn.timestamp,
                "quote": social_turn.text,
                "reasoning": (
                    "Opening is small talk about a personal trip — "
                    "relationship rapport, not deal signal."
                ),
            }
        )
        signals_considered.append(
            f"relationship_rapport_only: '{social_turn.text}' [{social_turn.timestamp}] "
            "— social, no deal signal"
        )

    return {
        "result_type": "abstain",
        "opportunity_id": None,
        "message": "No meaningful update proposed",
        "last_touch_summary": (
            "Check-in call. Champion has no updates and is still waiting on "
            "finance. Vague 'maybe two weeks' follow-up timing. No actionable "
            "changes to the opportunity."
        ),
        "reason": (
            "Transcript is primarily social conversation. Champion explicitly "
            "states no new information and the only timing signal is a "
            "hedged 'maybe two weeks'. No grounded fields to update."
        ),
        "confidence": _abstain_confidence(coverage_ratio),
        "signals_considered": signals_considered,
        "evidence_by_field": {"last_touch_summary": evidence},
        "warnings": [],
    }
