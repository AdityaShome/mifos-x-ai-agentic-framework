from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any

import httpx


@dataclass(slots=True)
class FineractClient:
    base_url: str
    tenant: str = "default"
    username: str = ""
    password: str = ""
    timeout: float = 300.0
    client: httpx.Client | None = None

    def _build_client(self) -> httpx.Client:
        headers = {
            "X-Mifos-Platform-TenantId": self.tenant,
            "Accept": "application/json",
        }
        auth = None
        if self.username or self.password:
            auth = (self.username, self.password)

        return httpx.Client(
            base_url=self.base_url.rstrip("/"),
            headers=headers,
            auth=auth,
            timeout=httpx.Timeout(self.timeout),
        )

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | list[Any] | None = None,
    ) -> dict[str, Any]:
        close_client = False
        client = self.client
        if client is None:
            client = self._build_client()
            close_client = True

        attempts = 3
        backoff = 0.5
        try:
            for attempt in range(1, attempts + 1):
                try:
                    response = client.request(method, path, params=params, json=json)
                    response.raise_for_status()
                    if not response.content:
                        return {}
                    return response.json()
                except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.RequestError):
                    if attempt == attempts:
                        raise
                    time.sleep(backoff * attempt)
                except httpx.HTTPStatusError:
                    # non-retryable HTTP error; re-raise
                    raise
        finally:
            if close_client:
                client.close()

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.request("GET", path, params=params)
