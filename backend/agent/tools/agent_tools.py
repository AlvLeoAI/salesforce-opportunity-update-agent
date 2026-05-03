"""LLM-callable tools for the agent loop.

These three tools are exposed to the model via OpenAI function calling. The
model decides which to invoke and when. The simulator mode in
`agent.clients` calls the same functions through a scripted plan so the local
demo path exercises the real tool code without a live API key.
"""
from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from agent.models import OpportunityUpdateDraft, Transcript


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_transcript",
            "description": (
                "Search the call transcript for turns matching a topic. Use "
                "queries like 'overview', 'pricing', 'budget', 'timeline', "
                "'decision makers', 'champion', 'economic buyer', 'competition', "
                "'risks', 'next steps', 'decision criteria', 'metrics', 'pain'. "
                "An 'overview' or empty query returns every turn."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Topic to look for in the transcript.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_signal_coverage",
            "description": (
                "Given a JSON object of fields you have transcript evidence "
                "for, return coverage_ratio and a recommendation: 'draft' "
                "(>= 0.4), 'review' (>= 0.2), or 'abstain' (< 0.2). Call this "
                "BEFORE composing the final JSON. Both 'draft' and 'review' "
                "produce a draft - 'review' just means lower confidence. Only "
                "'abstain' produces an AbstainResult."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "extracted_signals": {
                        "type": "string",
                        "description": (
                            "JSON object whose keys are field names you have "
                            "evidence for. Recognized keys: stage, amount_usd, "
                            "close_date, next_step, champion, economic_buyer, "
                            "decision_criteria, decision_process, paper_process, "
                            "competition, metrics, identify_pain, risks, "
                            "last_touch_summary. Values may be summaries; "
                            "null/empty values are treated as missing."
                        ),
                    }
                },
                "required": ["extracted_signals"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_draft",
            "description": (
                "Validate a proposed OpportunityUpdateDraft JSON against the "
                "schema. Returns {valid: bool, errors: [string]}. Iterate until "
                "valid before emitting the final answer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "draft": {
                        "type": "string",
                        "description": "JSON string of the proposed draft.",
                    }
                },
                "required": ["draft"],
            },
        },
    },
]


KEY_FIELDS: tuple[str, ...] = (
    "stage",
    "amount_usd",
    "close_date",
    "next_step",
    "champion",
    "economic_buyer",
    "decision_criteria",
    "decision_process",
    "paper_process",
    "competition",
    "metrics",
    "identify_pain",
    "risks",
    "last_touch_summary",
)


QUERY_SYNONYMS: dict[str, list[str]] = {
    "pricing": ["price", "$", "annual", "quarterly", "quote", "billing", "discount"],
    "budget": ["budget", "$", "approve"],
    "timeline": ["q3", "q4", "kickoff", "tuesday", "friday", "tonight", "weeks", "review", "month", "quarter"],
    "decision makers": ["cmo", "ceo", "vp", "signer", "stakeholder", "procurement", "ben"],
    "champion": ["champion", "internal"],
    "economic buyer": ["signer", "cmo", "ceo", "vp", "approver"],
    "competition": ["competitor", "competition", "alternative", "spoonshot", "in market"],
    "risks": ["concern", "risk", "worry", "delay", "slip", "competitive", "moved"],
    "next steps": ["send", "follow", "tuesday", "friday", "tonight", "ping", "loop in"],
    "decision criteria": ["criteria", "priority", "important", "speed", "#1", "#2"],
    "metrics": ["metric", "kpi", "roi", "improvement"],
    "pain": ["problem", "pain", "challenge", "struggle"],
    "stakeholders": ["stakeholder", "ben", "priya", "cmo"],
}


def execute_read_transcript(transcript: Transcript, query: str) -> dict[str, Any]:
    q = (query or "").lower().strip()
    if not q or q in {"all", "overview", "full", "everything"}:
        matches = list(transcript.turns)
    else:
        keywords: set[str] = set(_tokenize(q))
        for category, terms in QUERY_SYNONYMS.items():
            if category in q:
                keywords.update(t.lower() for t in terms)
        matches = []
        for turn in transcript.turns:
            text_l = turn.text.lower()
            if any(kw and kw in text_l for kw in keywords):
                matches.append(turn)

    return {
        "query": query,
        "match_count": len(matches),
        "matches": [
            {"timestamp": t.timestamp, "speaker": t.speaker, "text": t.text}
            for t in matches
        ],
    }


def execute_check_signal_coverage(extracted_signals_json: Any) -> dict[str, Any]:
    try:
        signals = _coerce_to_dict(extracted_signals_json, "extracted_signals")
    except ValueError as exc:
        return {"error": str(exc)}

    covered = sorted(f for f in KEY_FIELDS if _is_meaningful(signals.get(f)))
    missing = sorted(f for f in KEY_FIELDS if not _is_meaningful(signals.get(f)))
    coverage_ratio = round(len(covered) / len(KEY_FIELDS), 2)

    if coverage_ratio >= 0.4:
        recommendation = "draft"
    elif coverage_ratio < 0.2:
        recommendation = "abstain"
    else:
        recommendation = "review"

    return {
        "coverage_ratio": coverage_ratio,
        "covered_fields": covered,
        "missing_fields": missing,
        "recommendation": recommendation,
    }


def execute_validate_draft(draft_json: Any) -> dict[str, Any]:
    try:
        data = _coerce_to_dict(draft_json, "draft")
    except ValueError as exc:
        return {"valid": False, "errors": [str(exc)]}
    try:
        OpportunityUpdateDraft.model_validate(data)
    except ValidationError as exc:
        errors = [
            f"{'.'.join(str(p) for p in err['loc']) or '<root>'}: {err['msg']}"
            for err in exc.errors()
        ]
        return {"valid": False, "errors": errors}
    return {"valid": True, "errors": []}


def _coerce_to_dict(value: Any, field_name: str) -> dict[str, Any]:
    """Accept either a JSON string or an already-parsed dict.

    OpenAI function-calling normally hands tools a JSON STRING in their
    ``arguments`` field, but for parameters the model can also emit a JSON
    object literal that the SDK delivers as a dict. Both shapes need to
    work; otherwise the agent 500s the moment the model picks the literal
    form.
    """
    if value is None or value == "":
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, (str, bytes, bytearray)):
        try:
            parsed = json.loads(value or "{}")
        except json.JSONDecodeError as exc:
            raise ValueError(f"{field_name}: invalid JSON ({exc})") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"{field_name}: must be a JSON object")
        return parsed
    raise ValueError(
        f"{field_name}: expected JSON object (or JSON string), got {type(value).__name__}"
    )


def _tokenize(s: str) -> list[str]:
    out: list[str] = []
    for piece in s.replace("/", " ").split():
        clean = piece.strip(",.!?;:()[]\"'").lower()
        if len(clean) >= 2:
            out.append(clean)
    return out


def _is_meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, (list, dict, tuple)) and not value:
        return False
    return True
