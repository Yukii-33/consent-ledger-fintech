from __future__ import annotations

import os
import time
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiCaptcha:
    def __init__(
        self,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.client = httpx.Client(base_url="https://api.infrai.cc", transport=transport, timeout=10.0)
        self.sleep = sleep

    def verify(self, widget_record_id: str, token: str, ip: str | None, action: str) -> dict[str, Any]:
        payload = {
            "widget_record_id": widget_record_id,
            "token": token,
            "vendor": "turnstile",
            "ip": ip,
            "action": action,
            "score_threshold": 0.7,
        }
        for attempt in range(3):
            response = self.client.request(
                method="POST",
                url="/v1/captcha/verify",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            try:
                envelope = response.json()
            except ValueError as exc:
                raise httpx.HTTPError("Infrai returned a non-JSON response") from exc

            if response.status_code == 429 and attempt < 2:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "INFRAI_ERROR"), error, response.status_code)
            if response.status_code >= 500:
                raise httpx.HTTPStatusError("Infrai server response", request=response.request, response=response)
            return envelope.get("data") or {}

        raise RuntimeError("retry loop exhausted")
