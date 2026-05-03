from __future__ import annotations

from agent.models import AbstainResult
from agent.orchestrator import run_scenario


def test_thin_transcript_abstains_with_last_touch_summary(tmp_path, monkeypatch):
    monkeypatch.setenv("SALESFORCE_AGENT_FORCE_FALLBACK", "1")

    output = run_scenario(
        "thin_signal",
        output_path=tmp_path / "thin_signal_output.json",
        pretty=True,
        load_env=False,
    )

    assert output.scenario_id == "thin_signal"
    assert isinstance(output.result, AbstainResult)
    assert output.result.result_type == "abstain"
    assert "No meaningful update proposed" in output.result.message
    assert output.result.last_touch_summary
    assert output.result.reason
    assert output.result.confidence >= 0.8
    assert "simulator_demo" in " ".join(output.result.warnings)

    trace_blob = " | ".join(output.trace)
    assert "read_transcript" in trace_blob
    assert "check_signal_coverage" in trace_blob
    assert "recommendation='abstain'" in trace_blob


def test_thin_transcript_has_touch_summary_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("SALESFORCE_AGENT_FORCE_FALLBACK", "1")

    output = run_scenario(
        "thin_signal",
        output_path=tmp_path / "thin_signal_output.json",
        load_env=False,
    )

    evidence_items = output.result.evidence_by_field["last_touch_summary"]
    assert evidence_items
    assert evidence_items[0].timestamp == "00:14"
    assert "waiting to hear back from finance" in evidence_items[0].quote
    assert evidence_items[0].reasoning


def test_thin_transcript_has_no_proposed_opportunity_update_payload(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("SALESFORCE_AGENT_FORCE_FALLBACK", "1")

    output = run_scenario(
        "thin_signal",
        output_path=tmp_path / "thin_signal_output.json",
        load_env=False,
    )
    payload = output.result.model_dump()

    assert payload["result_type"] == "abstain"
    assert "stage" not in payload
    assert "amount_usd" not in payload
    assert "close_date" not in payload
    assert "next_step" not in payload
    assert "meddpicc" not in payload
    assert "risks" not in payload
