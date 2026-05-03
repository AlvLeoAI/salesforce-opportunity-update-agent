# CLI Contract: Local Agent

## Purpose

The CLI is the only runtime interface for the local agent. It reads local mock
transcripts, runs the explicit orchestration flow, validates output, and writes
JSON artifacts for the static UI.

## Commands

### Run both required scenarios

```bash
python backend/run_agent.py --all
```

**Behavior**:
- Reads `backend/data/transcripts/rich_signal.txt`.
- Reads `backend/data/transcripts/thin_signal.txt`.
- Writes `backend/outputs/rich_signal_output.json`.
- Writes `backend/outputs/thin_signal_output.json`.
- Exits non-zero if either scenario fails schema validation or required evidence
  coverage.

### Run one scenario

```bash
python backend/run_agent.py --scenario rich_signal
python backend/run_agent.py --scenario thin_signal
```

**Options**:
- `--scenario`: `rich_signal` or `thin_signal`
- `--input`: optional path override for a transcript fixture
- `--output`: optional output JSON path override
- `--pretty`: optional pretty-printed JSON output

## Exit Codes

- `0`: Output generated and validated successfully.
- `1`: Input transcript missing or unreadable.
- `2`: Structured output generation failed.
- `3`: Pydantic validation failed.
- `4`: Evidence coverage failed.
- `5`: Unexpected orchestration error.

## Console Output

The CLI prints a concise run summary:

```text
rich_signal: draft written to backend/outputs/rich_signal_output.json
thin_signal: abstain written to backend/outputs/thin_signal_output.json
validation: passed
```

Errors must identify the scenario and failed step without printing secrets.

## Required Orchestration Steps

1. `transcript_reader`: load and parse transcript text.
2. `signal_extractor`: extract candidate opportunity signals with evidence.
3. `uncertainty_check`: decide draft vs abstain.
4. `schema_validator`: validate draft/abstain output and evidence coverage.
5. `orchestrator`: write JSON artifact and trace.
