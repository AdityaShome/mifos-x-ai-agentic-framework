from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskTier(str, Enum):
    HEALTHY = "Healthy"
    WATCH = "Watch"
    AT_RISK = "At Risk"
    CRITICAL = "Critical"


class ActionStatus(str, Enum):
    MONITOR_ONLY = "Monitor only"
    GENERATE_REMINDER_DRAFT = "Generate reminder draft"
    RECOMMEND_FOLLOW_UP = "Recommend follow-up"
    CREATE_FOLLOW_UP_TASK = "Create follow-up task"
    ESCALATE_TO_LOAN_OFFICER = "Escalate to loan officer"
    WRITE_AUDIT_LOG = "Write audit log"


class Client(BaseModel):
    client_id: str
    display_name: str
    external_id: str | None = None
    status: str = "active"
    office_id: str | None = None
    assigned_user_id: str | None = None


class Loan(BaseModel):
    loan_id: str
    client_id: str
    principal: float = Field(ge=0)
    outstanding_balance: float = Field(ge=0)
    overdue_amount: float = Field(ge=0)
    days_past_due: int = Field(default=0, ge=0)
    missed_installments: int = Field(default=0, ge=0)
    repayment_history_score: float = Field(default=0, ge=0, le=100)
    recent_activity_score: float = Field(default=0, ge=0, le=100)
    currency: str = "USD"
    status: str = "active"


class RepaymentSchedule(BaseModel):
    schedule_id: str
    loan_id: str
    due_date: datetime
    principal_due: float = Field(ge=0)
    interest_due: float = Field(ge=0)
    fees_due: float = Field(ge=0)
    penalties_due: float = Field(ge=0)
    total_due: float = Field(ge=0)
    total_paid: float = Field(ge=0)
    is_overdue: bool = False


class RiskFactor(BaseModel):
    name: str
    weight: float
    raw_value: float
    normalized_value: float
    contribution: float
    explanation: str


class RiskScore(BaseModel):
    loan_id: str
    client_id: str
    score: int = Field(ge=0, le=100)
    tier: RiskTier
    factor_breakdown: list[RiskFactor] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    computed_at: datetime = Field(default_factory=datetime.utcnow)


class AgentDecision(BaseModel):
    loan_id: str
    client_id: str
    risk_score: int = Field(ge=0, le=100)
    risk_tier: RiskTier
    evidence: dict[str, Any] = Field(default_factory=dict)
    recommended_action: ActionStatus
    policy_decision: str
    explanation: str
    autonomy_level: int = Field(ge=0, le=4)
    model_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditLog(BaseModel):
    loan_id: str
    client_id: str
    risk_score: int = Field(ge=0, le=100)
    risk_tier: RiskTier
    evidence: dict[str, Any] = Field(default_factory=dict)
    recommended_action: ActionStatus
    policy_decision: str
    explanation: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    model_name: str
    autonomy_level: int = Field(ge=0, le=4)


class AutonomySettings(BaseModel):
    autonomy_level: int = Field(default=1, ge=0, le=4)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: str | None = None
