from __future__ import annotations

import json

from agent.models import AgentRunOutput
from agent.orchestrator import run_scenario
from agent.tools.schema_validator import validate_agent_output


def test_rich_output_json_validates_against_agent_schema(tmp_path, monkeypatch):
    monkeypatch.setenv("SALESFORCE_AGENT_FORCE_FALLBACK", "1")
    output_path = tmp_path / "rich_signal_output.json"

    output = run_scenario(
        "rich_signal",
        output_path=output_path,
        pretty=True,
        load_env=False,
    )

    parsed = AgentRunOutput.model_validate_json(output_path.read_text())
    assert parsed == output
    assert json.loads(output_path.read_text())["result"]["result_type"] == "draft"


def test_thin_output_json_validates_against_agent_schema(tmp_path, monkeypatch):
    monkeypatch.setenv("SALESFORCE_AGENT_FORCE_FALLBACK", "1")
    output_path = tmp_path / "thin_signal_output.json"

    output = run_scenario(
        "thin_signal",
        output_path=output_path,
        pretty=True,
        load_env=False,
    )

    parsed = AgentRunOutput.model_validate_json(output_path.read_text())
    assert parsed == output
    assert json.loads(output_path.read_text())["result"]["result_type"] == "abstain"


def test_schema_validator_warns_on_missing_evidence_does_not_raise(tmp_path, monkeypatch):
    """Missing evidence is advisory, not blocking.

    Production transcripts often have valid model inferences without explicit
    quotes (e.g. stage inferred from procurement + pricing context). The
    validator should surface that as a warning so the reviewer knows the
    field isn't transcript-anchored, but never reject the result.
    """
    from pathlib import Path

    monkeypatch.setenv("SALESFORCE_AGENT_FORCE_FALLBACK", "1")
    output = run_scenario(
        "rich_signal",
        output_path=tmp_path / "rich_signal_output.json",
        load_env=False,
    )
    transcript_text = (
        Path(__file__).resolve().parents[1] / "data" / "transcripts" / "rich_signal.txt"
    ).read_text()

    output.result.evidence_by_field.pop("stage")
    output.result.warnings.clear()

    validated = validate_agent_output(output, transcript_text=transcript_text)

    assert validated.result.result_type == "draft"
    assert validated.result.stage  # stage value retained, just lacks evidence
    assert any(
        "stage" in w and "no grounding quote" in w
        for w in validated.result.warnings
    ), validated.result.warnings
