from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.plugin.exceptions import PluginConfigError, PluginLoadError
from core.plugin.manifest import PluginManifest


@dataclass(slots=True)
class PluginPackage:
    """A discoverable plugin package rooted at a directory containing plugin.yaml."""

    root: Path
    manifest_path: Path
    manifest: PluginManifest

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def version(self) -> str:
        return self.manifest.version

    @property
    def dependencies(self) -> list[str]:
        return list(self.manifest.dependencies)


def resolve_load_order(packages: list[PluginPackage]) -> list[PluginPackage]:
    """Topological sort by declared plugin dependencies. Raises on cycles or missing deps."""
    by_name = {pkg.name: pkg for pkg in packages}
    if len(by_name) != len(packages):
        raise PluginConfigError("duplicate plugin package names in discovery set")

    for pkg in packages:
        for dep in pkg.dependencies:
            if dep not in by_name:
                raise PluginLoadError(f"plugin {pkg.name!r} depends on missing package {dep!r}")

    visited: set[str] = set()
    visiting: set[str] = set()
    ordered: list[PluginPackage] = []

    def visit(name: str) -> None:
        if name in visited:
            return
        if name in visiting:
            raise PluginLoadError(f"circular plugin dependency involving {name!r}")
        visiting.add(name)
        pkg = by_name[name]
        for dep in pkg.dependencies:
            visit(dep)
        visiting.remove(name)
        visited.add(name)
        ordered.append(pkg)

    for pkg in packages:
        visit(pkg.name)
    return ordered


@dataclass(slots=True)
class PackageIndex:
    """In-memory index of discovered plugin packages."""

    packages: list[PluginPackage] = field(default_factory=list)

    def by_name(self) -> dict[str, PluginPackage]:
        return {p.name: p for p in self.packages}

    def ordered(self) -> list[PluginPackage]:
        return resolve_load_order(self.packages)
