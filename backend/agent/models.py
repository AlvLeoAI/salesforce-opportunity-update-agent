from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    """Base model for UI-facing artifacts."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class ScenarioId(str, Enum):
    RICH_SIGNAL = "rich_signal"
    THIN_SIGNAL = "thin_signal"
    LIVE = "live"


class Stage(str, Enum):
    PROSPECTING = "prospecting"
    DISCOVERY = "discovery"
    SOLUTION_DESIGN = "solution_design"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class TranscriptTurn(StrictModel):
    timestamp: str
    speaker: str
    text: str

    @field_validator("timestamp", "speaker", "text")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be empty")
        return value


class Transcript(StrictModel):
    scenario_id: ScenarioId
    source_path: str
    raw_text: str
    turns: list[TranscriptTurn]
    warnings: list[str] = Field(default_factory=list)

    @field_validator("raw_text")
    @classmethod
    def require_raw_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("transcript raw_text must not be empty")
        return value


class Evidence(StrictModel):
    timestamp: str
    quote: str
    reasoning: str

    @field_validator("timestamp", "quote", "reasoning")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("evidence fields must not be empty")
        return value


class NextStep(StrictModel):
    description: str | None = None
    owner: str | None = None
    due_date: date | None = None

    @field_validator("description", "owner", mode="before")
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class MEDDPICC(StrictModel):
    metrics: str | None = None
    economic_buyer: str | None = None
    decision_criteria: str | None = None
    decision_process: str | None = None
    paper_process: str | None = None
    identify_pain: str | None = None
    champion: str | None = None
    competition: str | None = None

    @field_validator(
        "metrics",
        "economic_buyer",
        "decision_criteria",
        "decision_process",
        "paper_process",
        "identify_pain",
        "champion",
        "competition",
        mode="before",
    )
    @classmethod
    def blank_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class OpportunityUpdateDraft(StrictModel):
    result_type: Literal["draft"] = "draft"
    opportunity_id: str
    stage: Stage
    amount_usd: float | None = None
    close_date: date | None = None
    next_step: NextStep = Field(default_factory=NextStep)
    meddpicc: MEDDPICC = Field(default_factory=MEDDPICC)
    risks: list[str] = Field(default_factory=list)
    last_touch_summary: str
    confidence: float = Field(ge=0, le=1)
    evidence_by_field: dict[str, list[Evidence]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("opportunity_id", "last_touch_summary")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("draft text fields must not be empty")
        return value


class AbstainResult(StrictModel):
    result_type: Literal["abstain"] = "abstain"
    opportunity_id: str | None = None
    message: str
    last_touch_summary: str
    reason: str
    confidence: float = Field(ge=0, le=1)
    signals_considered: list[str] = Field(default_factory=list)
    evidence_by_field: dict[str, list[Evidence]] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    @field_validator("message", "last_touch_summary", "reason")
    @classmethod
    def require_non_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("abstain text fields must not be empty")
        return value


AgentResult = Annotated[
    OpportunityUpdateDraft | AbstainResult,
    Field(discriminator="result_type"),
]


class AgentRunOutput(StrictModel):
    schema_version: str = "1.0"
    scenario_id: ScenarioId
    generated_at: datetime
    transcript_path: str
    result: AgentResult
    trace: list[str] = Field(default_factory=list)
