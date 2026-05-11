from fastapi import APIRouter, HTTPException

from app.api.schemas import DecisionFeedbackRequest, DecisionFeedbackResponse
from app.audit.logger import AuditLogger
from app.config import get_settings
from app.mifos_client.client import FineractClient
from app.agent.workflow import run_for_loan_id
from app.policy.autonomy import get_autonomy_level

router = APIRouter(prefix="/decisions", tags=["decisions"])

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


@router.get("/{loan_id}")
def get_decision(loan_id: str):
	decision = _audit_logger.get_latest_decision(loan_id)
	if decision is not None:
		return decision

	try:
		return run_for_loan_id(
			fineract_client=_fineract_client(),
			loan_id=loan_id,
			autonomy_level=get_autonomy_level(),
			ollama_base_url=_settings.ollama_base_url,
			model_name=_settings.ollama_model,
			audit_logger=_audit_logger,
		)
	except Exception as exc:
		raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{loan_id}/feedback", response_model=DecisionFeedbackResponse)
def submit_feedback(loan_id: str, payload: DecisionFeedbackRequest) -> DecisionFeedbackResponse:
	record = _audit_logger.record_feedback(
		loan_id=loan_id,
		feedback=payload.feedback,
		comment=payload.comment,
		reviewer=payload.reviewer,
	)
	return DecisionFeedbackResponse(
		loan_id=record["loan_id"],
		feedback=record["feedback"],
		comment=record["comment"],
		reviewer=record["reviewer"],
		stored=True,
	)
