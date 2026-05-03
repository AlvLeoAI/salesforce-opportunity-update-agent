# Data Model: Salesforce Opportunity Update Agent

## Transcript

**Purpose**: Source call text used for grounded opportunity-update extraction.

**Fields**:
- `scenario_id`: enum `rich_signal`, `thin_signal`
- `source_path`: string path to local transcript fixture
- `raw_text`: full transcript text
- `turns`: list of TranscriptTurn

**Validation Rules**:
- `raw_text` must not be empty.
- `scenario_id` must match the fixture being processed.
- Malformed timestamps are preserved in raw text but marked as parser warnings.

## TranscriptTurn

**Purpose**: Timestamped speaker utterance parsed from a transcript.

**Fields**:
- `timestamp`: string, expected timestamp from transcript
- `speaker`: string
- `text`: string

**Validation Rules**:
- `text` must not be empty after trimming.
- `timestamp` should follow the fixture timestamp format when present.

## Evidence

**Purpose**: Field-level support for a proposed Salesforce update.

**Fields**:
- `timestamp`: string
- `quote`: exact transcript quote
- `reasoning`: short explanation of why the quote supports the field

**Validation Rules**:
- `timestamp`, `quote`, and `reasoning` are required.
- `quote` must be an exact substring of the source transcript or associated
  transcript turn text.
- Evidence cannot be reused to support unrelated field values without a distinct
  reasoning note.

## NextStep

**Purpose**: Proposed next action for the opportunity.

**Fields**:
- `description`: string or null
- `owner`: string or null
- `due_date`: ISO date string or null

**Validation Rules**:
- Non-empty fields require evidence keyed by `next_step.description`,
  `next_step.owner`, or `next_step.due_date`.
- `due_date` must be a valid ISO date when present.

## MEDDPICC

**Purpose**: Deal qualification notes extracted from the transcript.

**Fields**:
- `metrics`: string or null
- `economic_buyer`: string or null
- `decision_criteria`: string or null
- `decision_process`: string or null
- `paper_process`: string or null
- `identify_pain`: string or null
- `champion`: string or null
- `competition`: string or null

**Validation Rules**:
- Every non-empty field requires evidence keyed by `meddpicc.<field_name>`.
- Unsupported values remain null or empty according to the final model design.

## OpportunityUpdateDraft

**Purpose**: Reviewable Salesforce opportunity update proposal.

**Fields**:
- `result_type`: literal `draft`
- `opportunity_id`: string
- `stage`: enum `prospecting`, `discovery`, `solution_design`, `proposal`,
  `negotiation`, `closed_won`, `closed_lost`
- `amount_usd`: number or null
- `close_date`: ISO date string or null
- `next_step`: NextStep
- `meddpicc`: MEDDPICC
- `risks`: list of strings
- `last_touch_summary`: string
- `confidence`: float from 0 to 1
- `evidence_by_field`: map of field path to list of Evidence
- `warnings`: list of strings

**Validation Rules**:
- `confidence` must be between 0 and 1.
- `stage` must be one of the allowed enum values.
- `close_date` must be a valid ISO date when present.
- Each non-empty proposed field must have evidence in `evidence_by_field`.
- Risk evidence uses paths such as `risks[0]`, `risks[1]`.
- `last_touch_summary` must be present for UI review.

## AbstainResult

**Purpose**: First-class state for transcripts without enough meaningful update
signal.

**Fields**:
- `result_type`: literal `abstain`
- `opportunity_id`: string or null
- `message`: literal or display text containing `No meaningful update proposed`
- `last_touch_summary`: string
- `reason`: string explaining why no update was proposed
- `confidence`: float from 0 to 1 for the abstention decision
- `signals_considered`: list of short signal labels
- `warnings`: list of strings

**Validation Rules**:
- Must not include proposed opportunity field updates.
- `last_touch_summary` is required.
- `message` must be clear enough for the UI abstain state.

## AgentRunOutput

**Purpose**: Top-level JSON artifact consumed by the UI.

**Fields**:
- `schema_version`: string
- `scenario_id`: enum `rich_signal`, `thin_signal`
- `generated_at`: ISO datetime string
- `transcript_path`: string
- `result`: OpportunityUpdateDraft or AbstainResult
- `trace`: lightweight list of completed orchestration steps

**Validation Rules**:
- `result_type` discriminates draft vs abstain.
- `schema_version` increments only for breaking output contract changes.
- `trace` must include transcript read, signal extraction, uncertainty check,
  schema validation, and output write steps.

## State Transitions

```text
Transcript fixture
  -> Transcript parsed
  -> Candidate signals extracted with evidence
  -> Signal sufficiency checked
  -> Draft result OR Abstain result
  -> Pydantic validation
  -> JSON output written
  -> Static UI renders review state
```
