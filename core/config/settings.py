from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "swp-automation"
    environment: str = "development"
    log_level: str = "INFO"
    plugin_paths: list[str] = Field(default_factory=lambda: ["modules"])

    model_config = SettingsConfigDict(
        env_prefix="SWP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
