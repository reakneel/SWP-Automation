from __future__ import annotations

from uuid import uuid4

from core.task.base import TaskContext, TaskResult
from core.task.registry import TaskRegistry


class TaskExecutor:
    """Executes registered tasks and provides a stable worker boundary."""

    def __init__(self, registry: TaskRegistry) -> None:
        self.registry = registry

    async def execute(self, task_name: str, metadata: dict | None = None) -> TaskResult:
        task = self.registry.get(task_name)
        context = TaskContext(run_id=str(uuid4()), metadata=metadata or {})
        return await task.run(context)
