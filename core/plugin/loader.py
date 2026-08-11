from __future__ import annotations

from pathlib import Path

from .discovery import PluginDiscovery
from .importer import PluginImporter


class PluginLoader:
    """Load plugins from discovered manifests."""

    def __init__(
        self,
    ) -> None:
        self.discovery = PluginDiscovery()
        self.importer = PluginImporter()

    def discover(
        self,
        paths: list[Path],
    ) -> list[Path]:
        return self.discovery.discover(paths)

    def load_class(
        self,
        module_name: str,
        class_name: str,
    ) -> type:
        return self.importer.load_class(
            module_name,
            class_name,
        )
