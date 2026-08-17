from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "swp-automation"
    environment: str = "development"
    log_level: str = "INFO"
    plugin_paths: list[str] = Field(default_factory=lambda: ["modules", "packages"])
    plugin_module_prefixes: list[str] = Field(default_factory=lambda: ["modules.", "packages."])
    plugin_strict_permissions: bool = False
    execution_timeout_seconds: float = 300.0
    metadata_max_keys: int = 64
    metadata_max_value_length: int = 4096
    redis_url: str | None = None
    task_queue_key: str = "automation:tasks"
    worker_id: str = "worker-1"
    worker_poll_timeout: float = 1.0
    api_keys: list[str] = Field(default_factory=list)
    rate_limit_per_minute: int = 120
    audit_max_events: int = 5000
    ai_api_key: str | None = None
    ai_base_url: str | None = "https://api.x.ai/v1"
    ai_model: str | None = "grok-3"

    model_config = SettingsConfigDict(
        env_prefix="SWP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
