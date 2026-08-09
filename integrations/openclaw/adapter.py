from __future__ import annotations

from typing import Any

from core.runtime import AutomationRuntime


class OpenClawAdapter:
    """Thin, framework-neutral boundary for exposing automation to OpenClaw."""

    def __init__(self, runtime: AutomationRuntime) -> None:
        self.runtime = runtime

    async def list_tasks(self) -> list[dict[str, Any]]:
        return [
            {"name": task.name, "description": task.description}
            for task in self.runtime.registry.all()
        ]

    async def run_task(self, task_name: str) -> dict[str, Any]:
        record = await self.runtime.executor.execute(task_name)
        return record.to_dict()

    async def get_run(self, run_id: str) -> dict[str, Any] | None:
        record = await self.runtime.store.get(run_id)
        return record.to_dict() if record else None

    async def health(self) -> dict[str, Any]:
        return {"status": "ok", "tasks": len(self.runtime.registry.all())}
