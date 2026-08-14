from __future__ import annotations

from pathlib import Path

from core.plugin.base import Plugin
from core.plugin.exceptions import PluginLoadError
from core.plugin.loader import PluginLoader
from core.plugin.registry import PluginEntry, PluginRegistry
from core.plugin.state import PluginState
from core.task.base import Task
from core.task.registry import TaskRegistry


class PluginManager:
    """Own plugin lifecycle: discover → load → register tasks → startup/shutdown."""

    def __init__(
        self,
        registry: TaskRegistry,
        plugin_registry: PluginRegistry | None = None,
        loader: PluginLoader | None = None,
    ) -> None:
        self.registry = registry
        self.plugin_registry = plugin_registry or PluginRegistry()
        self.loader = loader or PluginLoader()
        self._plugins: dict[str, Plugin] = {}

    async def load(self, plugin: Plugin, *, manifest: object | None = None) -> None:
        name = plugin.metadata.name
        if name in self._plugins:
            raise ValueError(f"Plugin already loaded: {name}")

        self._plugins[name] = plugin
        for task in plugin.tasks():
            if not isinstance(task, Task):
                raise TypeError(f"Plugin {name} returned a non-Task object")
            self.registry.register(task)

        if manifest is not None:
            entry = PluginEntry(plugin=plugin, manifest=manifest, state=PluginState.LOADED)
            if self.plugin_registry.get(name) is None:
                self.plugin_registry.register(entry)
            else:
                existing = self.plugin_registry.get(name)
                if existing is not None:
                    existing.state = PluginState.LOADED
                    existing.plugin = plugin

        try:
            await plugin.startup()
            entry = self.plugin_registry.get(name)
            if entry is not None:
                entry.state = PluginState.INITIALIZED
        except Exception as exc:
            entry = self.plugin_registry.get(name)
            if entry is not None:
                entry.state = PluginState.FAILED
            raise PluginLoadError(f"plugin startup failed for {name}: {exc}") from exc

    async def load_from_paths(self, paths: list[Path]) -> list[Plugin]:
        """Discover manifests under paths, instantiate, and load into the runtime."""
        loaded: list[Plugin] = []
        for plugin, manifest in self.loader.load_from_paths(paths):
            if self.plugin_registry.get(manifest.name) is None:
                self.plugin_registry.register(
                    PluginEntry(plugin=plugin, manifest=manifest, state=PluginState.DISCOVERED)
                )
            await self.load(plugin, manifest=manifest)
            loaded.append(plugin)
        return loaded

    async def unload(self, name: str) -> None:
        plugin = self._plugins.pop(name, None)
        if plugin is None:
            raise KeyError(name)
        await plugin.shutdown()
        entry = self.plugin_registry.get(name)
        if entry is not None:
            entry.state = PluginState.STOPPED
            self.plugin_registry.remove(name)

    def list(self) -> list[Plugin]:
        return list(self._plugins.values())

    def get(self, name: str) -> Plugin | None:
        return self._plugins.get(name)
