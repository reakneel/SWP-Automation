from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from core.plugin.base import Plugin
from core.plugin.exceptions import PluginLoadError
from core.plugin.loader import PluginLoader
from core.plugin.registry import PluginEntry, PluginRegistry
from core.plugin.state import PluginState
from core.task.base import Task
from core.task.registry import TaskRegistry


@dataclass(slots=True)
class PluginLoadReport:
    loaded: list[Plugin] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failed


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
        self._lock = asyncio.Lock()

    async def load(self, plugin: Plugin, *, manifest: object | None = None) -> None:
        name = plugin.metadata.name
        async with self._lock:
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
                self._plugins.pop(name, None)
                raise PluginLoadError(f"plugin startup failed for {name}: {exc}") from exc

    async def load_from_paths(self, paths: list[Path]) -> list[Plugin]:
        """Discover manifests under paths; isolate failures so one bad plugin does not abort the batch."""
        report = await self.load_from_paths_report(paths)
        return report.loaded

    async def load_from_paths_report(self, paths: list[Path]) -> PluginLoadReport:
        report = PluginLoadReport()
        for manifest_path in self.loader.discover(paths):
            try:
                plugin, manifest = self.loader.load_manifest(manifest_path)
            except Exception as exc:
                report.failed.append((str(manifest_path), str(exc)))
                continue

            if self.plugin_registry.get(manifest.name) is None:
                self.plugin_registry.register(
                    PluginEntry(plugin=plugin, manifest=manifest, state=PluginState.DISCOVERED)
                )

            try:
                await self.load(plugin, manifest=manifest)
                report.loaded.append(plugin)
            except Exception as exc:
                entry = self.plugin_registry.get(manifest.name)
                if entry is not None:
                    entry.state = PluginState.FAILED
                report.failed.append((manifest.name, str(exc)))
        return report

    async def unload(self, name: str) -> None:
        async with self._lock:
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
