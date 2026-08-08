from __future__ import annotations

from collections.abc import Iterable

from core.task.base import Task


class TaskRegistry:
    """In-memory registry mapping stable task names to task implementations."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def register(self, task: Task) -> None:
        if not task.name:
            raise ValueError("task.name must not be empty")
        if task.name in self._tasks:
            raise ValueError(f"task already registered: {task.name}")
        self._tasks[task.name] = task

    def register_many(self, tasks: Iterable[Task]) -> None:
        for task in tasks:
            self.register(task)

    def get(self, name: str) -> Task:
        try:
            return self._tasks[name]
        except KeyError as exc:
            raise KeyError(f"unknown task: {name}") from exc

    def list(self) -> list[Task]:
        return sorted(self._tasks.values(), key=lambda task: task.name)

    def names(self) -> list[str]:
        return [task.name for task in self.list()]
