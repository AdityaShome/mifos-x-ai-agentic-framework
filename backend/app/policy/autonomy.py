from enum import IntEnum

from threading import Lock

from app.risk.schemas import AutonomySettings


class AutonomyLevel(IntEnum):
    OBSERVE_ONLY = 0
    RECOMMEND_ONLY = 1
    DRAFT_ACTIONS_ONLY = 2
    AUTO_EXECUTE_LOW_RISK = 3
    AUTO_ESCALATE_CRITICAL_ONLY = 4


_AUTONOMY_LOCK = Lock()
_AUTONOMY_SETTINGS = AutonomySettings(autonomy_level=1)


def get_autonomy_settings() -> AutonomySettings:
    with _AUTONOMY_LOCK:
        return _AUTONOMY_SETTINGS.model_copy()


def set_autonomy_level(autonomy_level: int, updated_by: str | None = None) -> AutonomySettings:
    with _AUTONOMY_LOCK:
        _AUTONOMY_SETTINGS.autonomy_level = autonomy_level
        _AUTONOMY_SETTINGS.updated_by = updated_by
        return _AUTONOMY_SETTINGS.model_copy()


def get_autonomy_level() -> int:
    return get_autonomy_settings().autonomy_level
