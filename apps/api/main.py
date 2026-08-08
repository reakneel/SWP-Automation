from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.config.settings import get_settings
from core.runtime import runtime

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")


class TaskRunRequest(BaseModel):
    metadata: dict[str, object] = Field(default_factory=dict)


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "environment": settings.environment, "tasks": len(runtime.registry.names())}


@app.get("/api/v1/tasks")
async def list_tasks() -> list[dict[str, str]]:
    return [{"name": task.name, "description": task.description} for task in runtime.registry.list()]


@app.post("/api/v1/tasks/{task_name}/run")
async def run_task(task_name: str, request: TaskRunRequest) -> dict[str, object]:
    try:
        record = await runtime.executor.execute(task_name, request.metadata)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _serialize_run(record)


@app.get("/api/v1/runs")
async def list_runs(limit: int = 100) -> list[dict[str, object]]:
    limit = max(1, min(limit, 1000))
    return [_serialize_run(record) for record in runtime.executions.list(limit)]


@app.get("/api/v1/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, object]:
    record = runtime.executions.get(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="run not found")
    return _serialize_run(record)


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
