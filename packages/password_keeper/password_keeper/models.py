"""Vault models and legacy key cleanup."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

VAULT_VERSION = 2

ALLOWED_EXTRA_KEYS = frozenset(
    {
        "notes",
        "otp_uri",
        "tags",
        "browser",
        "http_realm",
        "form_action",
    }
)

LEGACY_VAULT_KEYS = frozenset(
    {
        "passwords",
        "items",
        "secrets",
        "kv",
        "key_values",
        "data",
    }
)


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class AccountEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    origin: str = ""
    username: str = ""
    secret_enc: str = ""
    label: str = ""
    source: str = "manual"
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    last_used_at: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)

    def public_dict(self, *, reveal_secret: str | None = None) -> dict[str, Any]:
        d: dict[str, Any] = {
            "id": self.id,
            "origin": self.origin,
            "username": self.username,
            "label": self.label or self.origin or self.username,
            "source": self.source,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_used_at": self.last_used_at,
            "extra": {k: v for k, v in self.extra.items() if k in ALLOWED_EXTRA_KEYS},
        }
        if reveal_secret is not None:
            d["password"] = reveal_secret
        else:
            d["password"] = "********"
        return d


class VaultDocument(BaseModel):
    version: int = VAULT_VERSION
    salt_b64: str
    master_fp: str
    accounts: list[AccountEntry] = Field(default_factory=list)
    legacy_discarded_keys: list[str] = Field(default_factory=list)


def normalize_origin(value: str) -> str:
    v = (value or "").strip()
    return v.rstrip("/")


def account_match_key(origin: str, username: str) -> str:
    return f"{normalize_origin(origin).lower()}|{username.strip().lower()}"
