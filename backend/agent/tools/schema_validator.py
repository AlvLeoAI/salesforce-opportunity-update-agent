from __future__ import annotations

import re

from agent.models import (
    AbstainResult,
    AgentResult,
    AgentRunOutput,
    OpportunityUpdateDraft,
    Transcript,
)


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

# Live LLM outputs paraphrase quotes more often than not. We accept an exact
# substring match first (the static fixtures rely on this) and fall back to a
# windowed token-overlap match for paraphrased quotes. The threshold is
# deliberately loose - we want renderable results with a visible warning, not
# a 422 to the reviewer. See WRITEUP.md for the trade-off discussion.
FUZZY_MATCH_THRESHOLD = 0.8
FUZZY_WINDOW_SLACK = 5

_WORD_RE = re.compile(r"\w+")


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

    if normalized.result.result_type in ("draft", "abstain"):
        raw_text = transcript.raw_text if transcript is not None else transcript_text
        if raw_text is None:
            raise SchemaValidationError("transcript text is required for evidence validation")
        scrub_warnings = _scrub_evidence(normalized.result, raw_text)
        if scrub_warnings:
            normalized.result.warnings.extend(scrub_warnings)

    if normalized.result.result_type == "draft":
        validate_evidence_coverage(normalized.result, raw_text)
    elif normalized.result.result_type == "abstain":
        validate_abstain_result(normalized.result, raw_text)

    return normalized


def validate_evidence_coverage(draft: OpportunityUpdateDraft, transcript_text: str) -> None:
    """Every populated field must have at least one evidence item.

    Quote matching against the transcript happens earlier in ``_scrub_evidence``
    (fuzzy, lenient). By the time we reach this check, any remaining evidence
    item has already been verified to match. If a populated field has no
    evidence at all, that's a real model failure and we still raise so the
    orchestrator's self-correction retry has a chance to fix it.
    """
    for field_path in populated_draft_field_paths(draft):
        evidence_items = draft.evidence_by_field.get(field_path)
        if not evidence_items:
            raise EvidenceCoverageError(f"missing evidence for populated field '{field_path}'")


def validate_abstain_result(result: AbstainResult, transcript_text: str) -> None:
    # Note: opportunity-update fields (stage, amount_usd, etc.) cannot appear
    # on AbstainResult because the model uses extra="forbid"; Pydantic rejects
    # them at parse time. Nothing to re-check here.

    if "No meaningful update proposed" not in result.message:
        raise SchemaValidationError("abstain message must clearly state no update")

    # ``last_touch_summary`` is the value itself; supporting evidence is nice
    # to have but not required. If the model omitted it (or every quote got
    # scrubbed earlier), surface a warning so the reviewer knows the summary
    # isn't transcript-anchored - never 422.
    if not result.evidence_by_field.get("last_touch_summary"):
        result.warnings.append(
            "evidence_filter: abstain last_touch_summary has no transcript "
            "evidence; the summary is shown as-is without grounding quotes"
        )


def quote_matches_transcript(
    quote: str,
    transcript_text: str,
    threshold: float = FUZZY_MATCH_THRESHOLD,
) -> bool:
    """True if quote is an exact substring or fuzzily matches a transcript window.

    Fuzzy match: tokenize quote and transcript into lowercase word tokens,
    slide a window of ``len(quote_tokens) + FUZZY_WINDOW_SLACK`` over the
    transcript tokens, and accept if any window contains at least
    ``threshold`` proportion of distinct quote tokens.
    """
    if not quote:
        return False
    if quote in transcript_text:
        return True

    quote_tokens = _tokenize(quote)
    transcript_tokens = _tokenize(transcript_text)
    if not quote_tokens or not transcript_tokens:
        return False

    quote_set = set(quote_tokens)
    needed = max(1, int(len(quote_set) * threshold))
    window_size = len(quote_tokens) + FUZZY_WINDOW_SLACK

    if len(transcript_tokens) <= window_size:
        return len(quote_set & set(transcript_tokens)) >= needed

    for start in range(0, len(transcript_tokens) - window_size + 1):
        window = set(transcript_tokens[start : start + window_size])
        if len(quote_set & window) >= needed:
            return True
    return False


def _tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in _WORD_RE.finditer(text)]


def _scrub_evidence(result: AgentResult, transcript_text: str) -> list[str]:
    """Drop evidence items whose quote can't be matched against the transcript.

    For drafts, also clear the value of any field whose evidence list is left
    empty so the reviewer never sees an unsupported value. ``stage`` is the
    one exception: it has no null sentinel, so we keep the stage value but
    flag it loudly in the warnings.
    """
    warnings: list[str] = []
    new_evidence: dict[str, list] = {}
    fully_dropped: set[str] = set()

    for field_path, items in result.evidence_by_field.items():
        kept = [item for item in items if quote_matches_transcript(item.quote, transcript_text)]
        if kept:
            new_evidence[field_path] = kept
            removed = len(items) - len(kept)
            if removed > 0:
                warnings.append(
                    f"evidence_filter: removed {removed} unmatched quote(s) for "
                    f"'{field_path}' (fuzzy threshold {FUZZY_MATCH_THRESHOLD})"
                )
        else:
            fully_dropped.add(field_path)
            warnings.append(
                f"evidence_filter: no quotes for '{field_path}' matched the "
                "transcript (exact or fuzzy); evidence entry removed"
            )

    result.evidence_by_field = new_evidence

    if isinstance(result, OpportunityUpdateDraft) and fully_dropped:
        warnings.extend(_clear_unevidenced_draft_fields(result, fully_dropped))

    return warnings


def _clear_unevidenced_draft_fields(
    draft: OpportunityUpdateDraft, dropped: set[str]
) -> list[str]:
    warnings: list[str] = []
    risk_indices_to_drop: set[int] = set()

    for path in dropped:
        if path == "stage":
            warnings.append(
                "evidence_filter: stage value retained despite no matching evidence; "
                "reviewer should verify before approving"
            )
        elif path == "amount_usd":
            draft.amount_usd = None
            warnings.append("evidence_filter: cleared amount_usd (no matching evidence)")
        elif path == "close_date":
            draft.close_date = None
            warnings.append("evidence_filter: cleared close_date (no matching evidence)")
        elif path.startswith("next_step."):
            attr = path.split(".", 1)[1]
            if hasattr(draft.next_step, attr):
                setattr(draft.next_step, attr, None)
                warnings.append(f"evidence_filter: cleared {path} (no matching evidence)")
        elif path.startswith("meddpicc."):
            attr = path.split(".", 1)[1]
            if hasattr(draft.meddpicc, attr):
                setattr(draft.meddpicc, attr, None)
                warnings.append(f"evidence_filter: cleared {path} (no matching evidence)")
        elif path.startswith("risks[") and path.endswith("]"):
            try:
                idx = int(path[len("risks[") : -1])
                risk_indices_to_drop.add(idx)
                warnings.append(f"evidence_filter: dropped {path} (no matching evidence)")
            except ValueError:
                pass

    if risk_indices_to_drop:
        rebuilt_risks: list[str] = []
        rebuilt_risk_evidence: dict[str, list] = {}
        new_idx = 0
        for old_idx, risk in enumerate(draft.risks):
            if old_idx in risk_indices_to_drop:
                continue
            rebuilt_risks.append(risk)
            old_key = f"risks[{old_idx}]"
            if old_key in draft.evidence_by_field:
                rebuilt_risk_evidence[f"risks[{new_idx}]"] = draft.evidence_by_field[old_key]
            new_idx += 1
        non_risk_evidence = {
            k: v for k, v in draft.evidence_by_field.items() if not k.startswith("risks[")
        }
        draft.evidence_by_field = {**non_risk_evidence, **rebuilt_risk_evidence}
        draft.risks = rebuilt_risks

    return warnings
