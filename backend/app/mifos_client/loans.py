from __future__ import annotations

from typing import Any

from app.mifos_client.client import FineractClient


def list_loans(client: FineractClient, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return client.get("/loans", params=params)


def get_loan(client: FineractClient, loan_id: str) -> dict[str, Any]:
    return client.get(f"/loans/{loan_id}")


def get_loan_repayment_schedule(client: FineractClient, loan_id: str) -> dict[str, Any]:
    return client.get(f"/loans/{loan_id}?associations=repaymentSchedule")
