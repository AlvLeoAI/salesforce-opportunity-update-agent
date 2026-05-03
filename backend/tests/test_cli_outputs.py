from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from agent.models import AgentRunOutput


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_all_writes_rich_and_thin_output_files(monkeypatch):
    env = os.environ.copy()
    env["SALESFORCE_AGENT_FORCE_FALLBACK"] = "1"

    result = subprocess.run(
        [sys.executable, "backend/run_agent.py", "--all"],
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    rich_path = PROJECT_ROOT / "backend" / "outputs" / "rich_signal_output.json"
    thin_path = PROJECT_ROOT / "backend" / "outputs" / "thin_signal_output.json"
    assert rich_path.exists()
    assert thin_path.exists()

    rich = AgentRunOutput.model_validate_json(rich_path.read_text())
    thin = AgentRunOutput.model_validate_json(thin_path.read_text())
    assert rich.result.result_type == "draft"
    assert thin.result.result_type == "abstain"
