import pytest

from app.risk.schemas import Loan, RiskTier
from app.risk.scoring import (
    calculate_days_past_due_factor,
    calculate_loan_balance_factor,
    calculate_missed_installments_factor,
    calculate_overdue_amount_factor,
    calculate_recent_activity_factor,
    calculate_repayment_history_factor,
    score_loan,
)


class TestFactorCalculations:
    """Unit tests for individual risk factor calculations."""

    def test_days_past_due_factor_zero(self):
        assert calculate_days_past_due_factor(0) == 0.0

    def test_days_past_due_factor_mid_range(self):
        factor = calculate_days_past_due_factor(30)
        assert 40.0 <= factor <= 60.0  # Approximately 50

    def test_days_past_due_factor_max(self):
        assert calculate_days_past_due_factor(60) == 100.0
        assert calculate_days_past_due_factor(90) == 100.0

    def test_overdue_amount_factor_zero(self):
        assert calculate_overdue_amount_factor(0.0, 1000.0) == 0.0

    def test_overdue_amount_factor_mid_range(self):
        factor = calculate_overdue_amount_factor(50.0, 1000.0)  # 5% overdue
        assert 0 <= factor <= 25.0

    def test_overdue_amount_factor_high(self):
        factor = calculate_overdue_amount_factor(300.0, 1000.0)  # 30% overdue
        assert factor == 100.0

    def test_missed_installments_factor_zero(self):
        assert calculate_missed_installments_factor(0) == 0.0

    def test_missed_installments_factor_one(self):
        factor = calculate_missed_installments_factor(1)
        assert 25.0 <= factor <= 40.0  # Approximately 33

    def test_missed_installments_factor_max(self):
        assert calculate_missed_installments_factor(3) == 100.0
        assert calculate_missed_installments_factor(5) == 100.0

    def test_repayment_history_factor_perfect(self):
        assert calculate_repayment_history_factor(100.0) == 0.0

    def test_repayment_history_factor_mid(self):
        assert calculate_repayment_history_factor(50.0) == 50.0

    def test_repayment_history_factor_poor(self):
        assert calculate_repayment_history_factor(0.0) == 100.0

    def test_loan_balance_factor_zero(self):
        assert calculate_loan_balance_factor(0.0, 1000.0) == 0.0

    def test_loan_balance_factor_half(self):
        assert calculate_loan_balance_factor(500.0, 1000.0) == 50.0

    def test_loan_balance_factor_full(self):
        assert calculate_loan_balance_factor(1000.0, 1000.0) == 100.0

    def test_recent_activity_factor_active(self):
        assert calculate_recent_activity_factor(100.0) == 0.0

    def test_recent_activity_factor_inactive(self):
        assert calculate_recent_activity_factor(0.0) == 100.0


class TestLoanScoring:
    """Unit tests for complete loan risk scoring."""

    def test_healthy_loan(self):
        loan = Loan(
            loan_id="L_HEALTHY",
            client_id="C001",
            principal=1000.0,
            outstanding_balance=450.0,
            overdue_amount=0.0,
            days_past_due=0,
            missed_installments=0,
            repayment_history_score=95.0,
            recent_activity_score=90.0,
        )
        score = score_loan(loan)
        assert score.score <= 30
        assert score.tier == RiskTier.HEALTHY

    def test_watch_loan(self):
        loan = Loan(
            loan_id="L_WATCH",
            client_id="C002",
            principal=2000.0,
            outstanding_balance=1400.0,
            overdue_amount=50.0,
            days_past_due=5,
            missed_installments=0,
            repayment_history_score=80.0,
            recent_activity_score=75.0,
        )
        score = score_loan(loan)
        assert 31 <= score.score <= 55
        assert score.tier == RiskTier.WATCH

    def test_at_risk_loan(self):
        loan = Loan(
            loan_id="L_AT_RISK",
            client_id="C003",
            principal=5000.0,
            outstanding_balance=3500.0,
            overdue_amount=300.0,
            days_past_due=25,
            missed_installments=1,
            repayment_history_score=60.0,
            recent_activity_score=50.0,
        )
        score = score_loan(loan)
        assert 56 <= score.score <= 75
        assert score.tier == RiskTier.AT_RISK

    def test_critical_loan(self):
        loan = Loan(
            loan_id="L_CRITICAL",
            client_id="C004",
            principal=3000.0,
            outstanding_balance=2800.0,
            overdue_amount=800.0,
            days_past_due=60,
            missed_installments=3,
            repayment_history_score=35.0,
            recent_activity_score=20.0,
        )
        score = score_loan(loan)
        assert score.score > 75
        assert score.tier == RiskTier.CRITICAL

    def test_score_has_factor_breakdown(self):
        loan = Loan(
            loan_id="L_TEST",
            client_id="C001",
            principal=1000.0,
            outstanding_balance=500.0,
            overdue_amount=10.0,
            days_past_due=2,
            missed_installments=0,
            repayment_history_score=85.0,
            recent_activity_score=80.0,
        )
        score = score_loan(loan)
        assert len(score.factor_breakdown) == 6
        assert all(f.weight > 0 for f in score.factor_breakdown)
        assert sum(f.weight for f in score.factor_breakdown) == 100

    def test_score_is_bounded(self):
        loan = Loan(
            loan_id="L_EXTREME",
            client_id="C001",
            principal=1000.0,
            outstanding_balance=2000.0,  # Extreme case
            overdue_amount=1000.0,
            days_past_due=180,
            missed_installments=10,
            repayment_history_score=0.0,
            recent_activity_score=0.0,
        )
        score = score_loan(loan)
        assert 0 <= score.score <= 100
