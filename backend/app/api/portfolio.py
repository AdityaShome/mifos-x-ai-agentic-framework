from fastapi import APIRouter, HTTPException, Query

from app.api.schemas import PortfolioHealthResponse, AgentRunRequest, AgentRunResponse
from app.agent.workflow import build_portfolio_health_response, run_for_loan_id
from app.audit.logger import AuditLogger
from app.config import get_settings
from app.mifos_client.client import FineractClient
from app.policy.autonomy import get_autonomy_level

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

_settings = get_settings()
_audit_logger = AuditLogger()


def _fineract_client() -> FineractClient:
	return FineractClient(
		base_url=_settings.fineract_base_url,
		tenant=_settings.fineract_tenant,
		username=_settings.fineract_username,
		password=_settings.fineract_password,
		timeout=_settings.fineract_timeout_seconds,
	)


@router.get("/health", response_model=PortfolioHealthResponse)
def portfolio_health(limit: int = Query(default=200, ge=1, le=500)) -> PortfolioHealthResponse:
	try:
		return build_portfolio_health_response(
			fineract_client=_fineract_client(),
			audit_logger=_audit_logger,
			autonomy_level=get_autonomy_level(),
			ollama_base_url=_settings.ollama_base_url,
			model_name=_settings.ollama_model,
			limit=limit,
		)
	except Exception as exc:
		raise HTTPException(status_code=502, detail=f"Unable to load portfolio data: {exc}") from exc


@router.get("/at-risk")
def at_risk_accounts(limit: int = Query(default=200, ge=1, le=500)):
	health = portfolio_health(limit=limit)
	return [item for item in health.items if item.risk_score >= 31]


@router.post("/agent/run", response_model=AgentRunResponse)
def run_agent(payload: AgentRunRequest) -> AgentRunResponse:
	try:
		if payload.loan_id:
			decision = run_for_loan_id(
				fineract_client=_fineract_client(),
				loan_id=payload.loan_id,
				autonomy_level=get_autonomy_level(),
				ollama_base_url=_settings.ollama_base_url,
				model_name=_settings.ollama_model,
				audit_logger=_audit_logger,
			)
			return AgentRunResponse(decisions=[decision])

		health = build_portfolio_health_response(
			fineract_client=_fineract_client(),
			audit_logger=_audit_logger,
			autonomy_level=get_autonomy_level(),
			ollama_base_url=_settings.ollama_base_url,
			model_name=_settings.ollama_model,
			limit=payload.limit or 200,
		)
		decisions = []
		for item in health.items:
			stored = _audit_logger.get_latest_decision(item.loan_id)
			if stored is not None:
				decisions.append(stored)
		return AgentRunResponse(decisions=decisions)
	except Exception as exc:
		raise HTTPException(status_code=502, detail=f"Unable to run agent: {exc}") from exc
