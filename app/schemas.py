from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


Severity = Literal[
    "low",
    "medium",
    "high",
    "critical"
]


IncidentStatus = Literal[
    "open",
    "investigating",
    "resolved"
]


class IncidentCreate(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=200
    )

    description: str = Field(
        min_length=5
    )

    severity: Severity


class IncidentUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=3,
        max_length=200
    )

    description: str | None = Field(
        default=None,
        min_length=5
    )

    severity: Severity | None = None
    status: IncidentStatus | None = None


class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: Severity
    status: IncidentStatus
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class AIAnalysisResponse(BaseModel):
    id: int
    incident_id: int
    summary: str
    likely_root_cause: str
    confidence: float
    troubleshooting_steps: list[str]
    recommended_action: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class WebhookIncidentCreate(BaseModel):
    source: str = Field(
        min_length=2,
        max_length=100
    )

    external_id: str = Field(
        min_length=1,
        max_length=200
    )

    title: str = Field(
        min_length=3,
        max_length=200
    )

    description: str = Field(
        min_length=5
    )

    severity: Severity

    auto_analyze: bool = True


class WebhookIngestResponse(BaseModel):
    duplicate: bool
    event_id: int
    source: str
    external_id: str
    incident: IncidentResponse
    analysis: AIAnalysisResponse | None = None
