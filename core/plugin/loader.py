from __future__ import annotations

from pathlib import Path

import yaml

from core.config.settings import get_settings
from core.plugin.base import Plugin
from core.plugin.discovery import PluginDiscovery
from core.plugin.exceptions import PluginConfigError, PluginLoadError
from core.plugin.importer import PluginImporter
from core.plugin.manifest import PluginManifest
from core.plugin.permissions import is_module_allowed, validate_permissions


class PluginLoader:
    """Discover, parse, import, and instantiate plugins from manifests."""

    def __init__(
        self,
        *,
        module_prefixes: list[str] | None = None,
        strict_permissions: bool | None = None,
    ) -> None:
        settings = get_settings()
        self.discovery = PluginDiscovery()
        self.importer = PluginImporter()
        self.module_prefixes = module_prefixes if module_prefixes is not None else list(settings.plugin_module_prefixes)
        self.strict_permissions = (
            strict_permissions if strict_permissions is not None else settings.plugin_strict_permissions
        )

    def discover(self, paths: list[Path]) -> list[Path]:
        return self.discovery.discover(paths)

    def load_class(self, module_name: str, class_name: str) -> type:
        return self.importer.load_class(module_name, class_name)

    def parse_manifest(self, path: Path) -> PluginManifest:
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise PluginLoadError(f"cannot read manifest: {path}") from exc
        except yaml.YAMLError as exc:
            raise PluginConfigError(f"invalid YAML in manifest: {path}") from exc

        if not isinstance(raw, dict):
            raise PluginConfigError(f"manifest must be a mapping: {path}")

        try:
            manifest = PluginManifest.model_validate(raw)
        except Exception as exc:
            raise PluginConfigError(f"invalid plugin manifest: {path}: {exc}") from exc

        if not is_module_allowed(manifest.entrypoint.module, self.module_prefixes):
            raise PluginLoadError(
                f"entrypoint module not allowed: {manifest.entrypoint.module} "
                f"(allowed prefixes: {', '.join(self.module_prefixes)})"
            )

        try:
            manifest.permissions = validate_permissions(
                manifest.permissions,
                strict=self.strict_permissions,
            )
        except Exception as exc:
            raise PluginConfigError(f"invalid permissions in {path}: {exc}") from exc

        return manifest

    def instantiate(self, manifest: PluginManifest) -> Plugin:
        try:
            plugin_cls = self.load_class(manifest.entrypoint.module, manifest.entrypoint.class_name)
        except Exception as exc:
            raise PluginLoadError(
                f"failed to import {manifest.entrypoint.module}.{manifest.entrypoint.class_name}: {exc}"
            ) from exc

        try:
            plugin = plugin_cls()
        except TypeError as exc:
            raise PluginLoadError(
                f"plugin {manifest.name} requires constructor arguments and cannot be auto-loaded: {exc}"
            ) from exc
        except Exception as exc:
            raise PluginLoadError(f"failed to instantiate plugin {manifest.name}: {exc}") from exc

        if not isinstance(plugin, Plugin):
            raise PluginLoadError(f"entrypoint is not a Plugin subclass: {manifest.name}")

        return plugin

    def load_manifest(self, path: Path) -> tuple[Plugin, PluginManifest]:
        manifest = self.parse_manifest(path)
        plugin = self.instantiate(manifest)
        return plugin, manifest

    def load_from_paths(self, paths: list[Path]) -> list[tuple[Plugin, PluginManifest]]:
        results: list[tuple[Plugin, PluginManifest]] = []
        for manifest_path in self.discover(paths):
            results.append(self.load_manifest(manifest_path))
        return results
