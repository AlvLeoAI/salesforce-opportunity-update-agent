"""Tool-calling agent loop.

The model decides which tools to call and when. The result type (draft vs.
abstain) is determined by the model after consulting check_signal_coverage,
not by any pre-loop scenario branching.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from agent.models import Transcript
from agent.tools.agent_tools import (
    TOOL_DEFINITIONS,
    execute_check_signal_coverage,
    execute_read_transcript,
    execute_validate_draft,
)


class AgentLoopError(RuntimeError):
    pass


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]
    call_id: str


@dataclass
class AssistantTurn:
    """One assistant response from the model (or simulator)."""

    content: str | None
    tool_calls: list[ToolCall]
    raw_message: dict[str, Any]


ChatFn = Callable[[list[dict[str, Any]], list[dict[str, Any]]], AssistantTurn]


SYSTEM_PROMPT = """You are a Salesforce opportunity update agent. You receive a sales call transcript and decide whether to propose a CRM update or abstain.

Tools available:
  1. read_transcript(query) - search the transcript for relevant turns.
  2. check_signal_coverage(extracted_signals) - given a JSON object of fields you have evidence for, returns coverage_ratio and a recommendation: "draft", "abstain", or "review".
  3. validate_draft(draft) - validate proposed JSON against the OpportunityUpdateDraft schema.

Workflow:
  1. Start with read_transcript(query="overview") to inspect the call.
  2. Do targeted reads for: pricing/budget, timeline, decision makers (champion, economic buyer), competition, risks, next steps, decision criteria, MEDDPICC.
  3. Call check_signal_coverage with the signals you found. Honor the recommendation:
       - "draft" (coverage_ratio >= 0.4): compose an OpportunityUpdateDraft JSON, validate it, then return it.
       - "review" (0.2 <= coverage_ratio < 0.4): also compose an OpportunityUpdateDraft, BUT set confidence close to coverage_ratio (e.g. 0.3-0.45) so the reviewer sees this is a low-confidence draft. Only populate fields you actually have evidence for - leave the rest null. "review" is NOT abstain; the reviewer wants the partial signal, just clearly flagged as preliminary.
       - "abstain" (coverage_ratio < 0.2): compose an AbstainResult JSON ("No meaningful update proposed").
  4. Every populated field MUST include evidence in evidence_by_field with the exact transcript quote and timestamp from a read_transcript result. Quotes must be exact substrings of what the tool returned.
  5. Every evidence item MUST be the object {"timestamp": str, "quote": str, "reasoning": str} - all three keys are required, including for abstain results. "reasoning" is one short sentence explaining why this quote supports this field. Never emit an evidence item without "reasoning".
  6. If a field has no supporting evidence, leave it null/empty - never fabricate.
  7. Confidence reflects the proportion of fields with strong, unambiguous evidence.

Final answer:
  Your final assistant message (no tool_calls) must be ONLY a JSON object - either an OpportunityUpdateDraft (with "result_type": "draft") or an AbstainResult (with "result_type": "abstain"). No prose, no markdown fences.

OpportunityUpdateDraft fields:
  result_type ("draft"), opportunity_id, stage (one of: prospecting, discovery, solution_design, proposal, negotiation, closed_won, closed_lost), amount_usd (number|null), close_date (ISO date|null), next_step {description, owner, due_date}, meddpicc {metrics, economic_buyer, decision_criteria, decision_process, paper_process, identify_pain, champion, competition}, risks (string[]), last_touch_summary, confidence (0-1), evidence_by_field (map of field_path -> [{timestamp, quote, reasoning}]), warnings ([]).

AbstainResult fields:
  result_type ("abstain"), opportunity_id (nullable), message ("No meaningful update proposed"), last_touch_summary, reason, confidence (0-1), signals_considered (string[]), evidence_by_field (map of field_path -> [{timestamp, quote, reasoning}]; must include a "last_touch_summary" entry whose evidence items each carry timestamp, quote, AND reasoning), warnings ([]).
"""


@dataclass
class AgentLoopOutput:
    final_json: str
    trace: list[str] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)


def build_user_prompt(transcript: Transcript) -> str:
    return (
        "Sales call transcript metadata:\n"
        f"  scenario_id: {transcript.scenario_id}\n"
        f"  source_path: {transcript.source_path}\n"
        f"  total_turns: {len(transcript.turns)}\n\n"
        "Use the tools to inspect this call, decide via check_signal_coverage, "
        "and produce the final JSON output."
    )


def run_agent_loop(
    transcript: Transcript,
    chat: ChatFn,
    max_iterations: int = 12,
    messages: list[dict[str, Any]] | None = None,
    trace: list[str] | None = None,
) -> AgentLoopOutput:
    """Run the tool-calling loop until the model emits a final JSON message.

    ``messages`` and ``trace`` may be supplied to resume an earlier run
    (e.g. after a validation failure prompts a self-correction turn). When
    omitted, a fresh conversation is started.
    """
    if messages is None:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(transcript)},
        ]
    if trace is None:
        trace = []

    for _ in range(max_iterations):
        turn = chat(messages, TOOL_DEFINITIONS)
        messages.append(turn.raw_message)

        if not turn.tool_calls:
            if not turn.content:
                raise AgentLoopError("agent returned no content and no tool calls")
            return AgentLoopOutput(final_json=turn.content, trace=trace, messages=messages)

        for call in turn.tool_calls:
            result = _dispatch_tool(transcript, call)
            trace.append(_format_trace_entry(call, result))
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.call_id,
                    "content": json.dumps(result),
                }
            )

    raise AgentLoopError(
        f"agent loop exceeded {max_iterations} iterations without final answer"
    )


def _dispatch_tool(transcript: Transcript, call: ToolCall) -> dict[str, Any]:
    if call.name == "read_transcript":
        return execute_read_transcript(transcript, call.arguments.get("query", ""))
    if call.name == "check_signal_coverage":
        return execute_check_signal_coverage(call.arguments.get("extracted_signals", "{}"))
    if call.name == "validate_draft":
        return execute_validate_draft(call.arguments.get("draft", "{}"))
    return {"error": f"unknown tool: {call.name}"}


def _format_trace_entry(call: ToolCall, result: dict[str, Any]) -> str:
    if call.name == "read_transcript":
        q = call.arguments.get("query", "")
        return f"read_transcript(query={q!r}) -> {result.get('match_count', 0)} matches"
    if call.name == "check_signal_coverage":
        rec = result.get("recommendation", "?")
        ratio = result.get("coverage_ratio", "?")
        return f"check_signal_coverage(coverage_ratio={ratio}, recommendation={rec!r})"
    if call.name == "validate_draft":
        return f"validate_draft(valid={result.get('valid', False)})"
    return f"{call.name}(...)"
