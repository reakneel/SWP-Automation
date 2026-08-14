from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.config.settings import Settings
from core.enterprise.auth import ApiKeyAuthenticator
from core.enterprise.platform import EnterprisePlatform
from core.enterprise.rate_limit import RateLimiter
from core.enterprise.tenant import TenantContext
from core.runtime import AutomationRuntime
from core.task.base import Task, TaskContext, TaskResult


def test_api_key_auth_disabled_when_empty() -> None:
    auth = ApiKeyAuthenticator([])
    assert auth.enabled is False
    assert auth.verify(None) is True


def test_api_key_auth_requires_key() -> None:
    auth = ApiKeyAuthenticator(["secret"])
    assert auth.enabled is True
    assert auth.verify(None) is False
    assert auth.verify("wrong") is False
    assert auth.verify("secret") is True


def test_rate_limiter_blocks_after_limit() -> None:
    limiter = RateLimiter(limit=2, window_seconds=60)
    assert limiter.check("t1").allowed is True
    assert limiter.check("t1").allowed is True
    assert limiter.check("t1").allowed is False


def test_audit_log_filters_by_tenant() -> None:
    platform = EnterprisePlatform.from_settings(Settings(api_keys=[], rate_limit_per_minute=100, audit_max_events=100))
    platform.audit_task_run(
        TenantContext(tenant_id="a", actor="u1"),
        task_name="x.run",
        run_id="1",
        status="success",
    )
    platform.audit_task_run(
        TenantContext(tenant_id="b", actor="u2"),
        task_name="y.run",
        run_id="2",
        status="failed",
    )
    events = platform.audit.list(tenant_id="a")
    assert len(events) == 1
    assert events[0].tenant_id == "a"


def test_readiness_includes_enterprise_checks() -> None:
    platform = EnterprisePlatform.from_settings(Settings(api_keys=["k"]))
    status = platform.readiness()
    assert status.checks["auth"] == "enabled"
    assert status.status in {"ok", "degraded"}


class PingTask(Task):
    name = "enterprise.ping"
    description = "ping"

    async def run(self, context: TaskContext) -> TaskResult:
        return TaskResult.ok("pong")


def test_api_run_records_audit_and_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    from apps.api import main as api_main

    api_main.enterprise = EnterprisePlatform.from_settings(Settings(api_keys=[], rate_limit_per_minute=1000))
    rt = AutomationRuntime.create()
    rt.registry.register(PingTask())
    monkeypatch.setattr(api_main, "runtime", rt)

    client = TestClient(api_main.app)
    response = client.post(
        "/api/v1/tasks/enterprise.ping/run",
        json={"metadata": {}, "tenant_id": "acme", "actor": "alice"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    assert body["tenant_id"] == "acme"
    assert body["actor"] == "alice"

    audit = client.get("/api/v1/admin/audit")
    assert audit.status_code == 200
    events = audit.json()
    assert any(e["tenant_id"] == "acme" and e["resource"] == "enterprise.ping" for e in events)


def test_api_rejects_invalid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from apps.api import main as api_main

    api_main.enterprise = EnterprisePlatform.from_settings(Settings(api_keys=["good-key"]))
    client = TestClient(api_main.app)
    response = client.get("/api/v1/tasks", headers={"X-API-Key": "bad"})
    assert response.status_code == 401
