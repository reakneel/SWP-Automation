"""OpenAI-compatible chat client (xAI / OpenAI / local gateways)."""
from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from core.config.settings import get_settings


class AiClientError(RuntimeError):
    pass


class OpenAICompatibleClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        s = get_settings()
        self.api_key = (api_key if api_key is not None else s.ai_api_key) or ""
        self.base_url = (base_url or s.ai_base_url or "https://api.x.ai/v1").rstrip("/")
        self.model = model or s.ai_model or "grok-3"
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.api_key.strip())

    def chat(self, *, system: str, user: str, temperature: float = 0.2) -> str:
        if not self.enabled:
            raise AiClientError("SWP_AI_API_KEY is not set")
        url = f"{self.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        body = json.dumps(payload).encode()
        req = Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode())
        except HTTPError as exc:
            detail = exc.read().decode(errors="replace")[:500]
            raise AiClientError(f"AI HTTP {exc.code}: {detail}") from exc
        except URLError as exc:
            raise AiClientError(f"AI request failed: {exc}") from exc
        try:
            return str(data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise AiClientError(f"unexpected AI response shape: {data!r}") from exc
