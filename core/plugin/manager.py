from __future__ import annotations

from core.plugin.base import Plugin
from core.task.base import Task
from core.task.registry import TaskRegistry


class PluginManager:
    def __init__(self, registry: TaskRegistry) -> None:
        self.registry = registry
        self._plugins: dict[str, Plugin] = {}

    async def load(self, plugin: Plugin) -> None:
        name = plugin.metadata.name
        if name in self._plugins:
            raise ValueError(f"Plugin already loaded: {name}")
        self._plugins[name] = plugin
        for task in plugin.tasks():
            if not isinstance(task, Task):
                raise TypeError(f"Plugin {name} returned a non-Task object")
            self.registry.register(task)
        await plugin.startup()

    async def unload(self, name: str) -> None:
        plugin = self._plugins.pop(name, None)
        if plugin is None:
            raise KeyError(name)
        await plugin.shutdown()

    def list(self) -> list[Plugin]:
        return list(self._plugins.values())
