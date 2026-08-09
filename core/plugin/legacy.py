from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from core.task.base import Task, TaskContext, TaskResult


class LegacyFunctionTask(Task):
    """Adapt an existing sync/async function into the platform Task contract."""

    def __init__(
        self,
        name: str,
        function: Callable[..., Any],
        description: str = "Legacy function adapter",
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.description = description
        self.function = function
        self.kwargs = kwargs

    async def run(self, context: TaskContext) -> TaskResult:
        result = self.function(**self.kwargs)
        if asyncio.iscoroutine(result):
            result = await result
        return TaskResult.ok("legacy task completed", result=result)
