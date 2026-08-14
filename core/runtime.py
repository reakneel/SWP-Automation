from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.events.bus import EventBus
from core.plugin.manager import PluginManager
from core.task.registry import TaskRegistry
from core.task.store import ExecutionStore
from core.worker.executor import TaskExecutor


@dataclass(slots=True)
class AutomationRuntime:
    registry: TaskRegistry
    executions: ExecutionStore
    events: EventBus
    executor: TaskExecutor
    plugins: PluginManager

    @classmethod
    def create(cls) -> "AutomationRuntime":
        registry = TaskRegistry()
        executions = ExecutionStore()
        events = EventBus()
        executor = TaskExecutor(registry, executions, events)
        plugins = PluginManager(registry)
        return cls(registry, executions, events, executor, plugins)

    async def load_plugins(self, paths: list[Path] | list[str]) -> list:
        """Load plugins discovered under the given filesystem paths."""
        resolved = [Path(p) for p in paths]
        return await self.plugins.load_from_paths(resolved)


runtime = AutomationRuntime.create()
