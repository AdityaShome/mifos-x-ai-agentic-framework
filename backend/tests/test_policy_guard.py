from app.policy.policy_guard import evaluate_policy, recommend_action_for_policy
from app.risk.schemas import ActionStatus, RiskTier


def test_observe_only_mode_restricts_to_monitoring() -> None:
    decision = evaluate_policy(RiskTier.WATCH, 0, ActionStatus.RECOMMEND_FOLLOW_UP)

    assert decision["allowed"] is True
    assert decision["allowed_action"] == ActionStatus.MONITOR_ONLY
    assert decision["risk_tier"] == RiskTier.WATCH.value


def test_low_risk_autonomy_recommends_follow_up() -> None:
    assert recommend_action_for_policy(RiskTier.WATCH, 1) == ActionStatus.RECOMMEND_FOLLOW_UP


def test_critical_cases_escalate() -> None:
    decision = evaluate_policy(RiskTier.CRITICAL, 4, ActionStatus.ESCALATE_TO_LOAN_OFFICER)

    assert decision["allowed"] is True
    assert decision["allowed_action"] == ActionStatus.ESCALATE_TO_LOAN_OFFICER
