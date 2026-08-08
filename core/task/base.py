from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class TaskContext:
    run_id: str
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TaskResult:
    success: bool
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, message: str = "", **data: Any) -> "TaskResult":
        return cls(success=True, message=message, data=data)

    @classmethod
    def failure(cls, message: str, **data: Any) -> "TaskResult":
        return cls(success=False, message=message, data=data)


class Task(ABC):
    """Base contract for every executable automation task."""

    name: str
    description: str = ""

    @abstractmethod
    async def run(self, context: TaskContext) -> TaskResult:
        raise NotImplementedError
