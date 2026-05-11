from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.risk.schemas import ActionStatus, AgentDecision, AutonomySettings, RiskTier


class PortfolioHealthItem(BaseModel):
    loan_id: str
    client_id: str
    client_name: str | None = None
    risk_score: int = Field(ge=0, le=100)
    risk_tier: RiskTier
    recommended_action: ActionStatus
    policy_decision: str
    explanation: str
    autonomy_level: int = Field(ge=0, le=4)


class PortfolioHealthSummary(BaseModel):
    total_loans: int
    healthy_loans: int
    watch_loans: int
    at_risk_loans: int
    critical_loans: int


class PortfolioHealthResponse(BaseModel):
    summary: PortfolioHealthSummary
    items: list[PortfolioHealthItem]


class DecisionFeedbackRequest(BaseModel):
    feedback: Literal["approve", "reject"]
    comment: str | None = None
    reviewer: str | None = None


class DecisionFeedbackResponse(BaseModel):
    loan_id: str
    feedback: Literal["approve", "reject"]
    comment: str | None = None
    reviewer: str | None = None
    stored: bool = True


class AgentRunRequest(BaseModel):
    loan_id: str | None = None
    limit: int | None = Field(default=None, ge=1, le=500)


class AgentRunResponse(BaseModel):
    decisions: list[AgentDecision]


class AutonomyUpdateRequest(BaseModel):
    autonomy_level: int = Field(ge=0, le=4)
    updated_by: str | None = None


class AutonomySettingsResponse(AutonomySettings):
    pass
