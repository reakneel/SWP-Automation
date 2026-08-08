from __future__ import annotations

from dataclasses import dataclass

from core.events.bus import EventBus
from core.task.registry import TaskRegistry
from core.task.store import ExecutionStore
from core.worker.executor import TaskExecutor


@dataclass(slots=True)
class AutomationRuntime:
    registry: TaskRegistry
    executions: ExecutionStore
    events: EventBus
    executor: TaskExecutor

    @classmethod
    def create(cls) -> "AutomationRuntime":
        registry = TaskRegistry()
        executions = ExecutionStore()
        events = EventBus()
        executor = TaskExecutor(registry, executions, events)
        return cls(registry, executions, events, executor)


runtime = AutomationRuntime.create()
