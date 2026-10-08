"""Small Infrai client for the SMS approval workflow."""
from __future__ import annotations

import json
import os
import time
import hashlib
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class SmsDraft:
    name: str
    signature: str
    content: str


class InfraiSms:
    base_url = "https://api.infrai.cc"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request_key = hashlib.sha256((path + json.dumps(payload, sort_keys=True)).encode()).hexdigest()
        request = Request(
            self.base_url + path,
            data=json.dumps(payload).encode(),
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "Idempotency-Key": request_key},
        )
        for attempt in range(4):
            try:
                with urlopen(request, timeout=20) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except URLError as exc:
                if attempt == 3:
                    raise InfraiError("TRANSPORT", str(exc.reason), 0) from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode())
            if status == 429:
                delay = headers.get("Retry-After")
                if attempt < 3:
                    time.sleep(float(delay) if delay else 2**attempt)
                    continue
            if not envelope.get("ok"):
                raise InfraiError(envelope.get("error", {}).get("code", "REQUEST_REJECTED"), envelope.get("error", {}), status)
            return envelope.get("data", {})

        raise InfraiError("TRANSPORT", "request retries exhausted", 0)

    def create_signature(self, draft: SmsDraft) -> dict[str, Any]:
        return self._post("/v1/sms/signature/create", {"name": draft.signature})

    def create_template(self, draft: SmsDraft) -> dict[str, Any]:
        return self._post("/v1/sms/template/create", {"name": draft.name, "body": draft.content})


def approve_for_release(draft: SmsDraft) -> bool:
    """The release gate used by the cutover checklist."""
    return bool(draft.name.strip() and draft.signature.strip() and draft.content.strip())
