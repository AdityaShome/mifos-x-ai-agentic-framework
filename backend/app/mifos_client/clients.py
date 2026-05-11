from __future__ import annotations

from typing import Any

from app.mifos_client.client import FineractClient


def list_clients(client: FineractClient, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return client.get("/clients", params=params)


def get_client(client: FineractClient, client_id: str) -> dict[str, Any]:
    return client.get(f"/clients/{client_id}")
