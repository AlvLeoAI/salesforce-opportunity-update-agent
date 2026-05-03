from __future__ import annotations

from agent.models import OpportunityUpdateDraft
from agent.orchestrator import run_scenario


def test_rich_transcript_produces_draft_with_grounded_updates(tmp_path, monkeypatch):
    monkeypatch.setenv("SALESFORCE_AGENT_FORCE_FALLBACK", "1")

    output = run_scenario(
        "rich_signal",
        output_path=tmp_path / "rich_signal_output.json",
        pretty=True,
        load_env=False,
    )

    assert output.scenario_id == "rich_signal"
    assert isinstance(output.result, OpportunityUpdateDraft)
    assert output.result.result_type == "draft"
    assert output.result.stage == "negotiation"
    assert output.result.amount_usd == 120000
    assert output.result.close_date.isoformat() == "2026-10-01"
    assert output.result.confidence > 0.7
    assert len(output.result.risks) >= 2
    assert output.result.meddpicc.competition is not None
    assert "Spoonshot" in output.result.meddpicc.competition
    assert output.result.evidence_by_field
    assert "simulator_demo" in " ".join(output.result.warnings)

    trace_blob = " | ".join(output.trace)
    assert "read_transcript" in trace_blob
    assert "check_signal_coverage" in trace_blob
    assert "recommendation='draft'" in trace_blob
    assert "validate_draft(valid=True)" in trace_blob
