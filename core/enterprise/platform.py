from __future__ import annotations

from dataclasses import dataclass

from core.config.settings import Settings, get_settings
from core.enterprise.audit import AuditEvent, AuditLog
from core.enterprise.auth import ApiKeyAuthenticator
from core.enterprise.rate_limit import RateLimitResult, RateLimiter
from core.enterprise.tenant import TenantContext
from core.observability.health import HealthStatus, health_status


@dataclass(slots=True)
class EnterprisePlatform:
    """Facade for enterprise control-plane concerns."""

    auth: ApiKeyAuthenticator
    audit: AuditLog
    rate_limiter: RateLimiter
    settings: Settings

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> EnterprisePlatform:
        cfg = settings or get_settings()
        keys = list(cfg.api_keys) if cfg.api_keys else []
        return cls(
            auth=ApiKeyAuthenticator(keys),
            audit=AuditLog(max_events=cfg.audit_max_events),
            rate_limiter=RateLimiter(
                limit=cfg.rate_limit_per_minute,
                window_seconds=60.0,
            ),
            settings=cfg,
        )

    def authorize(self, api_key: str | None) -> bool:
        return self.auth.verify(api_key)

    def allow_request(self, tenant: TenantContext) -> RateLimitResult:
        return self.rate_limiter.check(tenant.tenant_id)

    def audit_task_run(
        self,
        tenant: TenantContext,
        *,
        task_name: str,
        run_id: str,
        status: str,
    ) -> AuditEvent:
        return self.audit.record(
            AuditEvent(
                action="task.run",
                tenant_id=tenant.tenant_id,
                actor=tenant.actor,
                resource=task_name,
                detail={"run_id": run_id, "status": status},
            )
        )

    def readiness(self, *, database: str = "ok", redis: str = "ok") -> HealthStatus:
        status = health_status(database=database, redis=redis)
        status.checks["auth"] = "enabled" if self.auth.enabled else "disabled"
        status.checks["rate_limit"] = "ok"
        status.checks["audit"] = "ok"
        if any(v not in {"ok", "disabled", "enabled"} for v in status.checks.values()):
            status.status = "degraded"
        return status
