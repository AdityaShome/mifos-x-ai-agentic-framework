from fastapi import APIRouter

from app.api.schemas import AutonomySettingsResponse, AutonomyUpdateRequest
from app.config import get_settings
from app.policy.autonomy import get_autonomy_settings, set_autonomy_level

router = APIRouter(prefix="/settings", tags=["settings"])

_settings = get_settings()


@router.get("/autonomy", response_model=AutonomySettingsResponse)
def read_autonomy_settings() -> AutonomySettingsResponse:
	return AutonomySettingsResponse(**get_autonomy_settings().model_dump())


@router.post("/autonomy", response_model=AutonomySettingsResponse)
def update_autonomy_settings(payload: AutonomyUpdateRequest) -> AutonomySettingsResponse:
	settings = set_autonomy_level(payload.autonomy_level, payload.updated_by)
	return AutonomySettingsResponse(**settings.model_dump())
