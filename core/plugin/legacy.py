from __future__ import annotations

import asyncio
import inspect
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
        if inspect.iscoroutinefunction(self.function):
            result = await self.function(**self.kwargs)
        else:
            result = await asyncio.to_thread(self.function, **self.kwargs)
        return TaskResult.ok("legacy task completed", result=result)
