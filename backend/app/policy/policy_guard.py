from __future__ import annotations

from app.risk.schemas import ActionStatus, RiskTier


def recommend_action_for_policy(risk_tier: RiskTier, autonomy_level: int) -> ActionStatus:
    if risk_tier == RiskTier.CRITICAL:
        return ActionStatus.ESCALATE_TO_LOAN_OFFICER

    if risk_tier == RiskTier.AT_RISK:
        return ActionStatus.CREATE_FOLLOW_UP_TASK if autonomy_level >= 2 else ActionStatus.RECOMMEND_FOLLOW_UP

    if risk_tier == RiskTier.WATCH:
        return ActionStatus.GENERATE_REMINDER_DRAFT if autonomy_level >= 2 else ActionStatus.RECOMMEND_FOLLOW_UP

    return ActionStatus.MONITOR_ONLY


def evaluate_policy(risk_tier: RiskTier, autonomy_level: int, recommended_action: ActionStatus) -> dict:
    allowed_action = recommend_action_for_policy(risk_tier, autonomy_level)

    if recommended_action != allowed_action:
        reason = f"Policy adjusted action from {recommended_action.value} to {allowed_action.value}."
    else:
        reason = f"Policy approved {allowed_action.value}."

    if risk_tier == RiskTier.CRITICAL and autonomy_level < 4:
        allowed_action = ActionStatus.ESCALATE_TO_LOAN_OFFICER
        reason = "Critical cases require human escalation unless autonomy level 4 is explicitly enabled."

    if autonomy_level <= 0:
        allowed_action = ActionStatus.MONITOR_ONLY
        reason = "Observe-only mode restricts action to monitoring and audit logging."

    return {
        "allowed": True,
        "allowed_action": allowed_action,
        "reason": reason,
        "risk_tier": risk_tier.value,
        "autonomy_level": autonomy_level,
        "requested_action": recommended_action.value,
    }
