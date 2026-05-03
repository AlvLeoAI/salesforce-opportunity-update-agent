from __future__ import annotations

from agent.models import AbstainResult, AgentRunOutput, OpportunityUpdateDraft, Transcript


class SchemaValidationError(RuntimeError):
    pass


class EvidenceCoverageError(SchemaValidationError):
    pass


REQUIRED_TRACE_ANCHORS = [
    "transcript_reader",
    "read_transcript",
    "check_signal_coverage",
    "schema_validator",
    "output_write",
]


def populated_draft_field_paths(draft: OpportunityUpdateDraft) -> list[str]:
    paths = ["stage"]

    if draft.amount_usd is not None:
        paths.append("amount_usd")
    if draft.close_date is not None:
        paths.append("close_date")

    if draft.next_step.description:
        paths.append("next_step.description")
    if draft.next_step.owner:
        paths.append("next_step.owner")
    if draft.next_step.due_date is not None:
        paths.append("next_step.due_date")

    for field_name in (
        "metrics",
        "economic_buyer",
        "decision_criteria",
        "decision_process",
        "paper_process",
        "identify_pain",
        "champion",
        "competition",
    ):
        if getattr(draft.meddpicc, field_name):
            paths.append(f"meddpicc.{field_name}")

    for index, risk in enumerate(draft.risks):
        if risk:
            paths.append(f"risks[{index}]")

    return paths


def validate_agent_output(
    output: AgentRunOutput, transcript: Transcript | None = None, transcript_text: str | None = None
) -> AgentRunOutput:
    normalized = AgentRunOutput.model_validate(output.model_dump())

    missing = [
        anchor
        for anchor in REQUIRED_TRACE_ANCHORS
        if not any(step.startswith(anchor) for step in normalized.trace)
    ]
    if missing:
        raise SchemaValidationError(
            f"missing trace anchors: {', '.join(missing)}"
        )

    if normalized.result.result_type == "draft":
        raw_text = transcript.raw_text if transcript is not None else transcript_text
        if raw_text is None:
            raise SchemaValidationError("transcript text is required for evidence validation")
        validate_evidence_coverage(normalized.result, raw_text)
    elif normalized.result.result_type == "abstain":
        raw_text = transcript.raw_text if transcript is not None else transcript_text
        if raw_text is None:
            raise SchemaValidationError("transcript text is required for abstain validation")
        validate_abstain_result(normalized.result, raw_text)

    return normalized


def validate_evidence_coverage(draft: OpportunityUpdateDraft, transcript_text: str) -> None:
    for field_path in populated_draft_field_paths(draft):
        evidence_items = draft.evidence_by_field.get(field_path)
        if not evidence_items:
            raise EvidenceCoverageError(f"missing evidence for populated field '{field_path}'")

        for item in evidence_items:
            if item.quote not in transcript_text:
                raise EvidenceCoverageError(
                    f"evidence quote for '{field_path}' is not present in transcript"
                )


def validate_abstain_result(result: AbstainResult, transcript_text: str) -> None:
    # Note: opportunity-update fields (stage, amount_usd, etc.) cannot appear
    # on AbstainResult because the model uses extra="forbid"; Pydantic rejects
    # them at parse time. Nothing to re-check here.

    if "No meaningful update proposed" not in result.message:
        raise SchemaValidationError("abstain message must clearly state no update")

    evidence_items = result.evidence_by_field.get("last_touch_summary")
    if not evidence_items:
        raise EvidenceCoverageError("missing evidence for abstain last_touch_summary")

    for item in evidence_items:
        if item.quote not in transcript_text:
            raise EvidenceCoverageError(
                "abstain evidence quote is not present in transcript"
            )
