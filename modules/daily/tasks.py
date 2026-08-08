from __future__ import annotations

from collections.abc import Awaitable, Callable

from core.task.base import Task, TaskContext, TaskResult


class DailyTask(Task):
    def __init__(self, name: str, description: str, handler: Callable[[TaskContext], Awaitable[dict]]) -> None:
        self.name = name
        self.description = description
        self._handler = handler

    async def run(self, context: TaskContext) -> TaskResult:
        data = await self._handler(context)
        return TaskResult.ok(f"{self.name} completed", **data)


async def default_cleanup(context: TaskContext) -> dict:
    return {"action": "cleanup", "dry_run": bool(context.metadata.get("dry_run", True))}


async def default_report(context: TaskContext) -> dict:
    return {"action": "report"}
