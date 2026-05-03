from __future__ import annotations

from agent.orchestrator import run_scenario
from agent.tools.schema_validator import populated_draft_field_paths


def test_every_populated_rich_draft_field_has_quote_timestamp_and_reasoning(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("SALESFORCE_AGENT_FORCE_FALLBACK", "1")

    output = run_scenario(
        "rich_signal",
        output_path=tmp_path / "rich_signal_output.json",
        load_env=False,
    )

    result = output.result
    field_paths = populated_draft_field_paths(result)

    assert "stage" in field_paths
    assert "next_step.description" in field_paths
    assert "meddpicc.competition" in field_paths
    assert "meddpicc.champion" in field_paths
    assert "risks[0]" in field_paths
    assert "risks[1]" in field_paths

    for field_path in field_paths:
        evidence_items = result.evidence_by_field[field_path]
        assert evidence_items, field_path
        for evidence in evidence_items:
            assert evidence.timestamp
            assert evidence.quote
            assert evidence.reasoning
