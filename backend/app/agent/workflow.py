from __future__ import annotations

from typing import Any

from app.agent.explanation_agent import generate_explanation
from app.audit.logger import AuditLogger
from app.api.schemas import PortfolioHealthItem, PortfolioHealthResponse, PortfolioHealthSummary
from app.mifos_client.client import FineractClient
from app.mifos_client.clients import get_client, list_clients
from app.mifos_client.loans import get_loan, list_loans
from app.policy.autonomy import get_autonomy_settings
from app.policy.policy_guard import evaluate_policy, recommend_action_for_policy
from app.risk.schemas import ActionStatus, AgentDecision, Client, Loan, RiskScore, RiskTier
from app.risk.scoring import score_loan


def _extract_items(payload: Any) -> list[dict[str, Any]]:
	if isinstance(payload, list):
		return [item for item in payload if isinstance(item, dict)]

	if isinstance(payload, dict):
		for key in ("pageItems", "items", "data", "content"):
			items = payload.get(key)
			if isinstance(items, list):
				return [item for item in items if isinstance(item, dict)]

	return []


def _extract_client_name(payload: dict[str, Any]) -> str | None:
	for key in ("displayName", "fullname", "name", "clientName"):
		value = payload.get(key)
		if isinstance(value, str) and value.strip():
			return value.strip()

	firstname = payload.get("firstname") or payload.get("firstName")
	lastname = payload.get("lastname") or payload.get("lastName")
	if isinstance(firstname, str) and isinstance(lastname, str):
		name = f"{firstname.strip()} {lastname.strip()}".strip()
		return name or None

	if isinstance(firstname, str) and firstname.strip():
		return firstname.strip()

	return None


def _extract_loan_identifier(payload: dict[str, Any]) -> str:
	for key in ("loanId", "id", "accountNo", "accountNumber"):
		value = payload.get(key)
		if value is not None:
			return str(value)
	return "unknown-loan"


def _extract_client_identifier(payload: dict[str, Any]) -> str:
	for key in ("clientId", "id", "client_id"):
		value = payload.get(key)
		if value is not None:
			return str(value)
	return "unknown-client"


def _extract_float(payload: dict[str, Any], *keys: str, default: float = 0.0) -> float:
	for key in keys:
		value = payload.get(key)
		if value is not None:
			try:
				return float(value)
			except (TypeError, ValueError):
				continue
	return default


def _extract_int(payload: dict[str, Any], *keys: str, default: int = 0) -> int:
	for key in keys:
		value = payload.get(key)
		if value is not None:
			try:
				return int(float(value))
			except (TypeError, ValueError):
				continue
	return default


def _extract_nested_float(payload: dict[str, Any], path: list[str], default: float = 0.0) -> float:
	current: Any = payload
	for key in path:
		if not isinstance(current, dict):
			return default
		current = current.get(key)
	try:
		return float(current)
	except (TypeError, ValueError):
		return default


def _derive_repayment_history_score(payload: dict[str, Any], days_past_due: int, missed_installments: int, overdue_amount: float, outstanding_balance: float) -> float:
	for key in ("repaymentHistoryScore", "repayment_history_score", "historyScore"):
		value = payload.get(key)
		if value is not None:
			try:
				return max(0.0, min(100.0, float(value)))
			except (TypeError, ValueError):
				continue

	overdue_ratio = 0.0
	if outstanding_balance > 0:
		overdue_ratio = max(0.0, min(1.0, overdue_amount / outstanding_balance))

	derived = 100.0 - (days_past_due * 1.5) - (missed_installments * 12.0) - (overdue_ratio * 55.0)
	return max(0.0, min(100.0, derived))


def _derive_recent_activity_score(payload: dict[str, Any], days_past_due: int, overdue_amount: float, outstanding_balance: float) -> float:
	for key in ("recentActivityScore", "recent_activity_score", "activityScore"):
		value = payload.get(key)
		if value is not None:
			try:
				return max(0.0, min(100.0, float(value)))
			except (TypeError, ValueError):
				continue

	days_since_activity = payload.get("daysSinceLastTransaction") or payload.get("daysSinceLastActivity")
	if days_since_activity is not None:
		try:
			derived = 100.0 - (float(days_since_activity) * 2.0)
			return max(0.0, min(100.0, derived))
		except (TypeError, ValueError):
			pass

	overdue_ratio = 0.0
	if outstanding_balance > 0:
		overdue_ratio = max(0.0, min(1.0, overdue_amount / outstanding_balance))

	derived = 100.0 - (days_past_due * 1.2) - (overdue_ratio * 45.0)
	return max(0.0, min(100.0, derived))


def loan_from_fineract_payload(payload: dict[str, Any]) -> Loan:
	principal = _extract_float(payload, "principal", "approvedPrincipal", "loanPrincipal", default=0.0)
	outstanding_balance = _extract_float(
		payload,
		"outstandingBalance",
		"outstandingLoanBalance",
		"loanBalance",
		"netDisbursalAmount",
		default=0.0,
	)
	overdue_amount = _extract_float(payload, "overdueAmount", "totalOverdue", default=0.0)
	if overdue_amount == 0.0:
		overdue_amount = _extract_nested_float(payload, ["summary", "totalOverdue"], default=0.0)
	if outstanding_balance == 0.0:
		outstanding_balance = _extract_nested_float(payload, ["summary", "totalOutstanding"], default=principal)

	principal = max(0.0, principal)
	outstanding_balance = max(0.0, outstanding_balance)
	overdue_amount = max(0.0, overdue_amount)

	days_past_due = _extract_int(payload, "daysPastDue", "daysInArrears", "daysPastDueAmount", default=0)
	missed_installments = _extract_int(payload, "missedInstallments", "delinquentInstallments", "numberOfRepaymentsMissed", default=0)
	repayment_history_score = _derive_repayment_history_score(payload, days_past_due, missed_installments, overdue_amount, outstanding_balance)
	recent_activity_score = _derive_recent_activity_score(payload, days_past_due, overdue_amount, outstanding_balance)

	return Loan(
		loan_id=_extract_loan_identifier(payload),
		client_id=_extract_client_identifier(payload),
		principal=principal,
		outstanding_balance=outstanding_balance,
		overdue_amount=overdue_amount,
		days_past_due=days_past_due,
		missed_installments=missed_installments,
		repayment_history_score=repayment_history_score,
		recent_activity_score=recent_activity_score,
		currency=str(payload.get("currency", {}).get("code") if isinstance(payload.get("currency"), dict) else payload.get("currency", "USD")),
		status=str(payload.get("status", payload.get("loanStatus", "active"))),
	)


def client_from_fineract_payload(payload: dict[str, Any]) -> Client:
	return Client(
		client_id=_extract_client_identifier(payload),
		display_name=_extract_client_name(payload) or _extract_client_identifier(payload),
		external_id=str(payload.get("externalId")) if payload.get("externalId") is not None else None,
		status=str(payload.get("status", "active")),
		office_id=str(payload.get("officeId")) if payload.get("officeId") is not None else None,
		assigned_user_id=str(payload.get("staffId")) if payload.get("staffId") is not None else None,
	)


def load_clients(fineract_client: FineractClient, limit: int = 200) -> list[Client]:
	results: list[Client] = []
	offset = 0
	page_size = min(limit, 100)
	while len(results) < limit:
		payload = list_clients(fineract_client, params={"limit": page_size, "offset": offset})
		items = _extract_items(payload)
		if not items:
			break
		for item in items:
			results.append(client_from_fineract_payload(item))
			if len(results) >= limit:
				break
		offset += page_size
	return results


def load_loans(fineract_client: FineractClient, limit: int = 200) -> list[Loan]:
	results: list[Loan] = []
	offset = 0
	page_size = min(limit, 100)
	while len(results) < limit:
		payload = list_loans(fineract_client, params={"limit": page_size, "offset": offset})
		items = _extract_items(payload)
		if not items:
			break
		for item in items:
			results.append(loan_from_fineract_payload(item))
			if len(results) >= limit:
				break
		offset += page_size
	return results


def recommend_action(risk_score: RiskScore, autonomy_level: int) -> ActionStatus:
	if risk_score.tier == RiskTier.CRITICAL:
		return ActionStatus.ESCALATE_TO_LOAN_OFFICER

	if risk_score.tier == RiskTier.AT_RISK:
		return ActionStatus.CREATE_FOLLOW_UP_TASK if autonomy_level >= 2 else ActionStatus.RECOMMEND_FOLLOW_UP

	if risk_score.tier == RiskTier.WATCH:
		return ActionStatus.GENERATE_REMINDER_DRAFT if autonomy_level >= 2 else ActionStatus.RECOMMEND_FOLLOW_UP

	return ActionStatus.MONITOR_ONLY


def build_agent_decision(
	loan: Loan,
	autonomy_level: int,
	ollama_base_url: str,
	model_name: str,
	audit_logger: AuditLogger,
) -> AgentDecision:
	risk_score = score_loan(loan)
	recommended_action = recommend_action(risk_score, autonomy_level)
	policy_decision = evaluate_policy(risk_score.tier, autonomy_level, recommended_action)
	explanation = generate_explanation(
		evidence=risk_score.evidence,
		risk_tier=risk_score.tier.value,
		policy_decision=policy_decision["allowed_action"].value,
		autonomy_level=autonomy_level,
		model_name=model_name,
		base_url=ollama_base_url,
	)

	decision = AgentDecision(
		loan_id=loan.loan_id,
		client_id=loan.client_id,
		risk_score=risk_score.score,
		risk_tier=risk_score.tier,
		evidence=risk_score.evidence,
		recommended_action=policy_decision["allowed_action"],
		policy_decision=policy_decision["reason"],
		explanation=explanation,
		autonomy_level=autonomy_level,
		model_name=model_name,
	)
	audit_logger.write(decision)
	return decision


def build_portfolio_health_response(
	fineract_client: FineractClient,
	audit_logger: AuditLogger,
	autonomy_level: int,
	ollama_base_url: str,
	model_name: str,
	limit: int = 200,
) -> PortfolioHealthResponse:
	loans = load_loans(fineract_client, limit=limit)
	clients = {client.client_id: client for client in load_clients(fineract_client, limit=limit)}

	items: list[PortfolioHealthItem] = []
	counts = {
		RiskTier.HEALTHY: 0,
		RiskTier.WATCH: 0,
		RiskTier.AT_RISK: 0,
		RiskTier.CRITICAL: 0,
	}

	for loan in loans:
		client = clients.get(loan.client_id)
		if client is None:
			payload = get_client(fineract_client, loan.client_id)
			if isinstance(payload, dict):
				client = client_from_fineract_payload(payload)
				clients[client.client_id] = client

		client_name = client.display_name if client is not None else None
		decision = build_agent_decision(loan, autonomy_level, ollama_base_url, model_name, audit_logger)
		counts[decision.risk_tier] += 1
		items.append(
			PortfolioHealthItem(
				loan_id=decision.loan_id,
				client_id=decision.client_id,
				client_name=client_name,
				risk_score=decision.risk_score,
				risk_tier=decision.risk_tier,
				recommended_action=decision.recommended_action,
				policy_decision=decision.policy_decision,
				explanation=decision.explanation,
				autonomy_level=decision.autonomy_level,
			)
		)

	return PortfolioHealthResponse(
		summary=PortfolioHealthSummary(
			total_loans=len(items),
			healthy_loans=counts[RiskTier.HEALTHY],
			watch_loans=counts[RiskTier.WATCH],
			at_risk_loans=counts[RiskTier.AT_RISK],
			critical_loans=counts[RiskTier.CRITICAL],
		),
		items=items,
	)


def run_for_loan_id(
	fineract_client: FineractClient,
	loan_id: str,
	autonomy_level: int,
	ollama_base_url: str,
	model_name: str,
	audit_logger: AuditLogger,
) -> AgentDecision:
	payload = get_loan(fineract_client, loan_id)
	if not isinstance(payload, dict):
		raise ValueError(f"Loan {loan_id} was not found")

	loan = loan_from_fineract_payload(payload)
	return build_agent_decision(loan, autonomy_level, ollama_base_url, model_name, audit_logger)
