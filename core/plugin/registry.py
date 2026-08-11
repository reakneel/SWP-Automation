from __future__ import annotations

from dataclasses import dataclass

from core.plugin.state import PluginState


@dataclass
class PluginEntry:
    plugin: object
    manifest: object
    state: PluginState = PluginState.DISCOVERED


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[str, PluginEntry] = {}

    def register(self, entry: PluginEntry) -> None:
        if entry.manifest.name in self._plugins:
            raise ValueError("plugin already registered")
        self._plugins[entry.manifest.name] = entry

    def get(self, name: str) -> PluginEntry | None:
        return self._plugins.get(name)

    def remove(self, name: str) -> None:
        self._plugins.pop(name, None)

    def list(self) -> list[PluginEntry]:
        return list(self._plugins.values())
