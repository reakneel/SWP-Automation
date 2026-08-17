"""Feature gate for LLM / agent skill paths (optional API key)."""
from __future__ import annotations

from dataclasses import dataclass

from core.config.settings import get_settings


@dataclass(frozen=True, slots=True)
class AiSettingsView:
    enabled: bool
    base_url: str | None
    model: str | None
    has_api_key: bool


def get_ai_settings() -> AiSettingsView:
    s = get_settings()
    key = (s.ai_api_key or "").strip()
    return AiSettingsView(
        enabled=bool(key),
        base_url=s.ai_base_url,
        model=s.ai_model,
        has_api_key=bool(key),
    )


def ai_enabled() -> bool:
    """True when an OpenAI-compatible API key is configured."""
    return get_ai_settings().enabled
