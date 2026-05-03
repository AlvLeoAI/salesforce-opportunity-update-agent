from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from agent.agent_loop import AgentLoopError, run_agent_loop
from agent.clients import build_chat_client
from agent.models import (
    AbstainResult,
    AgentResult,
    AgentRunOutput,
    OpportunityUpdateDraft,
    ScenarioId,
)
from agent.tools.schema_validator import (
    SchemaValidationError,
    validate_agent_output,
)
from agent.tools.transcript_reader import parse_transcript_text, read_transcript

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"

DEFAULT_TRANSCRIPTS = {
    ScenarioId.RICH_SIGNAL: BACKEND_ROOT / "data" / "transcripts" / "rich_signal.txt",
    ScenarioId.THIN_SIGNAL: BACKEND_ROOT / "data" / "transcripts" / "thin_signal.txt",
}
DEFAULT_OUTPUTS = {
    ScenarioId.RICH_SIGNAL: BACKEND_ROOT / "outputs" / "rich_signal_output.json",
    ScenarioId.THIN_SIGNAL: BACKEND_ROOT / "outputs" / "thin_signal_output.json",
}
IMPLEMENTED_SCENARIOS = [ScenarioId.RICH_SIGNAL, ScenarioId.THIN_SIGNAL]


class OrchestrationError(RuntimeError):
    pass


def default_output_path(scenario_id: ScenarioId | str) -> Path:
    scenario = ScenarioId(scenario_id)
    return DEFAULT_OUTPUTS[scenario]


def run_scenario(
    scenario_id: ScenarioId | str,
    *,
    input_path: str | Path | None = None,
    output_path: str | Path | None = None,
    pretty: bool = False,
    load_env: bool = True,
) -> AgentRunOutput:
    """Run the agent end-to-end for a given transcript.

    The ``scenario_id`` argument only controls which transcript file is
    loaded by default. It does NOT pre-decide whether the agent will draft
    or abstain — that decision is owned by the model (via the
    ``check_signal_coverage`` tool) inside ``run_agent_loop``.
    """
    if load_env:
        load_dotenv(PROJECT_ROOT / ".env", override=False)

    scenario = ScenarioId(scenario_id)
    if scenario not in IMPLEMENTED_SCENARIOS:
        raise NotImplementedError(f"{scenario.value} is not implemented")

    transcript_path = (
        Path(input_path) if input_path is not None else DEFAULT_TRANSCRIPTS[scenario]
    )
    target_output_path = (
        Path(output_path) if output_path is not None else DEFAULT_OUTPUTS[scenario]
    )

    transcript = read_transcript(transcript_path, scenario)
    validated = _run_agent_for_transcript(
        transcript=transcript,
        scenario=scenario,
        transcript_path_display=_display_path(transcript_path),
    )

    target_output_path.parent.mkdir(parents=True, exist_ok=True)
    target_output_path.write_text(
        validated.model_dump_json(indent=2 if pretty else None) + "\n",
        encoding="utf-8",
    )
    return validated


def run_live_transcript(
    raw_text: str,
    *,
    load_env: bool = True,
) -> AgentRunOutput:
    """Run the agent against a transcript supplied at runtime.

    Same loop and validation as ``run_scenario`` but the transcript comes
    from a string (e.g. an HTTP request body) and the result is returned
    in-memory rather than written to disk.
    """
    if load_env:
        load_dotenv(PROJECT_ROOT / ".env", override=False)

    if not raw_text or not raw_text.strip():
        raise OrchestrationError("transcript text must not be empty")

    transcript = parse_transcript_text(raw_text=raw_text, scenario_id=ScenarioId.LIVE)
    return _run_agent_for_transcript(
        transcript=transcript,
        scenario=ScenarioId.LIVE,
        transcript_path_display="<live>",
    )


def _run_agent_for_transcript(
    *,
    transcript,
    scenario: ScenarioId,
    transcript_path_display: str,
) -> AgentRunOutput:
    chat, mode_warnings = build_chat_client(transcript)
    loop_output = run_agent_loop(transcript, chat)

    extra_warnings = list(mode_warnings)

    try:
        return _finalize_output(
            loop_output=loop_output,
            transcript=transcript,
            scenario=scenario,
            transcript_path_display=transcript_path_display,
            extra_warnings=extra_warnings,
        )
    except (OrchestrationError, SchemaValidationError, ValidationError) as exc:
        # One self-correction attempt: surface the validation error back to
        # the model so it can fix the missing fields and re-emit the JSON.
        # Reuses the same chat session so the model still sees its tool
        # results — no re-running read_transcript / coverage check.
        correction = (
            "Your previous final JSON failed validation:\n\n"
            f"{exc}\n\n"
            "Fix the issue and return the complete corrected JSON as your next "
            "final assistant message (no tool_calls, no markdown fences). "
            "Remember: every populated field needs an evidence_by_field entry "
            "with at least one item containing timestamp, quote, AND reasoning. "
            "On abstain results, evidence_by_field must include a "
            "'last_touch_summary' entry with the same shape."
        )
        loop_output.messages.append({"role": "user", "content": correction})
        retry_output = run_agent_loop(
            transcript,
            chat,
            messages=loop_output.messages,
            trace=loop_output.trace,
        )
        extra_warnings.append(
            "self_correction: agent corrected an initial validation error "
            f"({type(exc).__name__}) before returning the final result."
        )
        return _finalize_output(
            loop_output=retry_output,
            transcript=transcript,
            scenario=scenario,
            transcript_path_display=transcript_path_display,
            extra_warnings=extra_warnings,
        )


def _finalize_output(
    *,
    loop_output,
    transcript,
    scenario: ScenarioId,
    transcript_path_display: str,
    extra_warnings: list[str],
) -> AgentRunOutput:
    result = _parse_final_result(loop_output.final_json)

    if extra_warnings:
        result.warnings.extend(extra_warnings)
    if transcript.warnings:
        result.warnings.extend(transcript.warnings)

    output = AgentRunOutput(
        schema_version="1.0",
        scenario_id=scenario,
        generated_at=datetime.now(timezone.utc),
        transcript_path=transcript_path_display,
        result=result,
        trace=["transcript_reader", *loop_output.trace, "schema_validator", "output_write"],
    )
    return validate_agent_output(output, transcript=transcript)


def _parse_final_result(final_json: str) -> AgentResult:
    cleaned = _strip_markdown_fences(final_json.strip())
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise OrchestrationError(f"agent did not return valid JSON: {exc}") from exc

    result_type = data.get("result_type")
    try:
        if result_type == "draft":
            return OpportunityUpdateDraft.model_validate(data)
        if result_type == "abstain":
            return AbstainResult.model_validate(data)
    except ValidationError as exc:
        raise OrchestrationError(f"agent output failed schema validation: {exc}") from exc
    raise OrchestrationError(f"unknown or missing result_type: {result_type!r}")


def _strip_markdown_fences(text: str) -> str:
    fence = re.compile(r"^```(?:json)?\s*([\s\S]*?)\s*```$", re.MULTILINE)
    m = fence.match(text)
    return m.group(1).strip() if m else text


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


__all__ = [
    "AgentLoopError",
    "IMPLEMENTED_SCENARIOS",
    "OrchestrationError",
    "default_output_path",
    "run_live_transcript",
    "run_scenario",
]
