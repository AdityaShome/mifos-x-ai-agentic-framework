from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any

from app.audit.models import AuditLog
from app.config import get_settings
from app.risk.schemas import AgentDecision


def _sqlite_path() -> Path:
    settings = get_settings()
    if settings.sqlite_url.startswith("sqlite:///"):
        return Path(settings.sqlite_url.removeprefix("sqlite:///"))
    return Path("portfolio_health.db")


class AuditLogger:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path is not None else _sqlite_path()
        self._lock = Lock()
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loan_id TEXT NOT NULL,
                    client_id TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    risk_tier TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    recommended_action TEXT NOT NULL,
                    policy_decision TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    autonomy_level INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS decision_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    loan_id TEXT NOT NULL,
                    feedback TEXT NOT NULL,
                    comment TEXT,
                    reviewer TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

    def write(self, record: AuditLog | AgentDecision) -> None:
        payload = record.model_dump(mode="json")
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_logs (
                    loan_id, client_id, risk_score, risk_tier, evidence,
                    recommended_action, policy_decision, explanation,
                    timestamp, model_name, autonomy_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["loan_id"],
                    payload["client_id"],
                    payload["risk_score"],
                    payload["risk_tier"],
                    json.dumps(payload.get("evidence", {})),
                    payload["recommended_action"],
                    payload["policy_decision"],
                    payload["explanation"],
                    payload.get("timestamp") or payload.get("created_at"),
                    payload["model_name"],
                    payload["autonomy_level"],
                ),
            )

    def get_latest_decision(self, loan_id: str) -> AuditLog | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM audit_logs
                WHERE loan_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (loan_id,),
            ).fetchone()

        if row is None:
            return None

        return AuditLog(
            loan_id=row["loan_id"],
            client_id=row["client_id"],
            risk_score=row["risk_score"],
            risk_tier=row["risk_tier"],
            evidence=json.loads(row["evidence"]),
            recommended_action=row["recommended_action"],
            policy_decision=row["policy_decision"],
            explanation=row["explanation"],
            timestamp=row["timestamp"],
            model_name=row["model_name"],
            autonomy_level=row["autonomy_level"],
        )

    def list_decisions(self, limit: int = 50) -> list[AuditLog]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM audit_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            AuditLog(
                loan_id=row["loan_id"],
                client_id=row["client_id"],
                risk_score=row["risk_score"],
                risk_tier=row["risk_tier"],
                evidence=json.loads(row["evidence"]),
                recommended_action=row["recommended_action"],
                policy_decision=row["policy_decision"],
                explanation=row["explanation"],
                timestamp=row["timestamp"],
                model_name=row["model_name"],
                autonomy_level=row["autonomy_level"],
            )
            for row in rows
        ]

    def record_feedback(self, loan_id: str, feedback: str, comment: str | None, reviewer: str | None) -> dict[str, Any]:
        from datetime import datetime, timezone

        created_at = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO decision_feedback (loan_id, feedback, comment, reviewer, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (loan_id, feedback, comment, reviewer, created_at),
            )

        return {
            "loan_id": loan_id,
            "feedback": feedback,
            "comment": comment,
            "reviewer": reviewer,
            "created_at": created_at,
        }

    def list_feedback(self, loan_id: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM decision_feedback"
        params: tuple[Any, ...] = ()
        if loan_id is not None:
            query += " WHERE loan_id = ?"
            params = (loan_id,)
        query += " ORDER BY id DESC"

        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()

        return [dict(row) for row in rows]
