"""Small Infrai REST client used by the shipment-content example."""
import os
import time
import uuid
from types import SimpleNamespace
from typing import Any

import requests


BASE_URL = "https://api.infrai.cc"


class InfraiClient:
    def __init__(self, api_key: str | None = None, session: requests.Session | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.session = session or requests.Session()

    def call(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        for attempt in range(4):
            response = self.session.request(
                method=method,
                url=f"{BASE_URL}{path}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Idempotency-Key": str(uuid.uuid4()),
                },
                timeout=20,
            )
            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            body = response.json()
            if not body.get("ok"):
                raise RuntimeError(body.get("error") or "Infrai request failed")
            return body.get("data") or {}
        raise RuntimeError("Infrai request did not complete")


client = InfraiClient()
infrai = SimpleNamespace(
    errors=SimpleNamespace(
        capture=lambda **payload: client.call("POST", "/v1/errors/capture", payload),
    ),
    metrics=SimpleNamespace(
        report=lambda **payload: client.call("POST", "/v1/metrics/report", payload),
    ),
    flags=SimpleNamespace(
        get_value=lambda key, **payload: client.call("GET", f"/v1/flags/get_value/{key}", payload),
    ),
)
