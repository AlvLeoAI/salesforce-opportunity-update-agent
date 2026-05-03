from __future__ import annotations

import re
from pathlib import Path

from agent.models import ScenarioId, Transcript, TranscriptTurn

TURN_RE = re.compile(r"^\[(?P<timestamp>[^\]]+)\]\s*(?P<speaker>[^:]+):\s*(?P<text>.+)$")
TIMESTAMP_RE = re.compile(r"^\d{2}:\d{2}(:\d{2})?$")


def read_transcript(path: str | Path, scenario_id: ScenarioId | str) -> Transcript:
    source_path = Path(path)
    raw_text = source_path.read_text(encoding="utf-8")
    return parse_transcript_text(
        raw_text=raw_text,
        scenario_id=scenario_id,
        source_path=str(source_path),
    )


def parse_transcript_text(
    raw_text: str,
    scenario_id: ScenarioId | str,
    source_path: str = "<live>",
) -> Transcript:
    turns: list[TranscriptTurn] = []
    warnings: list[str] = []

    for line_number, raw_line in enumerate(raw_text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        match = TURN_RE.match(line)
        if not match:
            warnings.append(f"line {line_number}: could not parse transcript turn")
            continue

        timestamp = match.group("timestamp").strip()
        if not TIMESTAMP_RE.match(timestamp):
            warnings.append(f"line {line_number}: malformed timestamp '{timestamp}'")

        turns.append(
            TranscriptTurn(
                timestamp=timestamp,
                speaker=match.group("speaker").strip(),
                text=match.group("text").strip(),
            )
        )

    if not turns:
        warnings.append("no parseable timestamped turns found")

    return Transcript(
        scenario_id=ScenarioId(scenario_id),
        source_path=source_path,
        raw_text=raw_text,
        turns=turns,
        warnings=warnings,
    )
