from __future__ import annotations

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from core.config.settings import get_settings
from core.enterprise.platform import EnterprisePlatform
from core.enterprise.tenant import TenantContext
from core.runtime import runtime

settings = get_settings()
enterprise = EnterprisePlatform.from_settings(settings)
app = FastAPI(title=settings.app_name, version="0.1.0")


class TaskRunRequest(BaseModel):
    metadata: dict[str, object] = Field(default_factory=dict)
    tenant_id: str | None = None
    actor: str | None = None


def _tenant_from_request(
    request: TaskRunRequest | None = None,
    x_tenant_id: str | None = None,
    x_actor: str | None = None,
) -> TenantContext:
    tenant_id = (request.tenant_id if request else None) or x_tenant_id
    actor = (request.actor if request else None) or x_actor
    return TenantContext.from_headers(tenant_id=tenant_id, actor=actor)


def _require_auth(x_api_key: str | None) -> None:
    if not enterprise.authorize(x_api_key):
        raise HTTPException(status_code=401, detail="invalid or missing API key")


def _require_rate_limit(tenant: TenantContext) -> None:
    result = enterprise.allow_request(tenant)
    if not result.allowed:
        raise HTTPException(
            status_code=429,
            detail=f"rate limit exceeded; retry after {result.reset_after_seconds:.0f}s",
            headers={"Retry-After": str(int(result.reset_after_seconds) + 1)},
        )


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "environment": settings.environment,
        "tasks": len(runtime.registry.names()),
    }


@app.get("/ready")
async def ready() -> dict[str, object]:
    return enterprise.readiness().as_dict()


@app.get("/api/v1/tasks")
async def list_tasks(x_api_key: str | None = Header(default=None)) -> list[dict[str, str]]:
    _require_auth(x_api_key)
    return [{"name": task.name, "description": task.description} for task in runtime.registry.list()]


@app.post("/api/v1/tasks/{task_name}/run")
async def run_task(
    task_name: str,
    request: TaskRunRequest,
    x_api_key: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None),
    x_actor: str | None = Header(default=None),
) -> dict[str, object]:
    _require_auth(x_api_key)
    tenant = _tenant_from_request(request, x_tenant_id, x_actor)
    _require_rate_limit(tenant)
    try:
        record = await runtime.executor.execute(task_name, request.metadata)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    enterprise.audit_task_run(
        tenant,
        task_name=task_name,
        run_id=record.run_id,
        status=record.status.value,
    )
    payload = _serialize_run(record)
    payload["tenant_id"] = tenant.tenant_id
    payload["actor"] = tenant.actor
    return payload


@app.get("/api/v1/runs")
async def list_runs(
    limit: int = 100,
    x_api_key: str | None = Header(default=None),
) -> list[dict[str, object]]:
    _require_auth(x_api_key)
    limit = max(1, min(limit, 1000))
    return [_serialize_run(record) for record in runtime.executions.list(limit)]


@app.get("/api/v1/runs/{run_id}")
async def get_run(
    run_id: str,
    x_api_key: str | None = Header(default=None),
) -> dict[str, object]:
    _require_auth(x_api_key)
    record = runtime.executions.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    return _serialize_run(record)


@app.get("/api/v1/admin/plugins")
async def admin_list_plugins(x_api_key: str | None = Header(default=None)) -> list[dict[str, object]]:
    _require_auth(x_api_key)
    plugins = runtime.plugins.list()
    return [
        {
            "name": p.metadata.name,
            "version": p.metadata.version,
            "description": p.metadata.description,
            "tasks": [t.name for t in p.tasks()],
        }
        for p in plugins
    ]


@app.get("/api/v1/admin/audit")
async def admin_list_audit(
    limit: int = 100,
    tenant_id: str | None = None,
    x_api_key: str | None = Header(default=None),
) -> list[dict[str, object]]:
    _require_auth(x_api_key)
    return [e.as_dict() for e in enterprise.audit.list(limit=limit, tenant_id=tenant_id)]


@app.get("/api/v1/admin/status")
async def admin_status(x_api_key: str | None = Header(default=None)) -> dict[str, object]:
    _require_auth(x_api_key)
    return {
        "environment": settings.environment,
        "tasks_registered": len(runtime.registry.names()),
        "plugins_loaded": len(runtime.plugins.list()),
        "auth_enabled": enterprise.auth.enabled,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "readiness": enterprise.readiness().as_dict(),
    }


def _serialize_run(record) -> dict[str, object]:
    return {
        "run_id": record.run_id,
        "task_name": record.task_name,
        "status": record.status.value,
        "message": record.message,
        "data": record.data,
        "error": record.error,
        "started_at": record.started_at,
        "finished_at": record.finished_at,
        "duration_ms": record.duration_ms,
    }
