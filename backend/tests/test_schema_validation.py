from __future__ import annotations

import json

import pytest

from agent.models import AgentRunOutput
from agent.orchestrator import run_scenario
from agent.tools.schema_validator import EvidenceCoverageError, validate_agent_output


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


def test_schema_validator_rejects_missing_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("SALESFORCE_AGENT_FORCE_FALLBACK", "1")
    output = run_scenario(
        "rich_signal",
        output_path=tmp_path / "rich_signal_output.json",
        load_env=False,
    )

    output.result.evidence_by_field.pop("stage")

    with pytest.raises(EvidenceCoverageError):
        validate_agent_output(output, transcript_text="proposal")
