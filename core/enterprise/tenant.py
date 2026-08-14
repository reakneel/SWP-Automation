from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TenantContext:
    """Identity for multi-tenant execution and audit attribution."""

    tenant_id: str = "default"
    actor: str = "anonymous"

    @classmethod
    def from_headers(
        cls,
        *,
        tenant_id: str | None = None,
        actor: str | None = None,
    ) -> TenantContext:
        return cls(
            tenant_id=(tenant_id or "default").strip() or "default",
            actor=(actor or "anonymous").strip() or "anonymous",
        )
