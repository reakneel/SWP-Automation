from __future__ import annotations

from pathlib import Path

import pytest

from core.plugin.exceptions import PluginLoadError
from core.plugin.loader import PluginLoader
from core.plugin.manifest import PluginEntrypoint, PluginManifest
from core.plugin.package import PluginPackage, resolve_load_order
from core.runtime import AutomationRuntime


def _pkg(name: str, deps: list[str], root: Path) -> PluginPackage:
    manifest = PluginManifest(
        name=name,
        version="1.0.0",
        category="test",
        entrypoint=PluginEntrypoint(module=f"modules.{name}.plugin", class_name="X"),
        dependencies=deps,
    )
    return PluginPackage(root=root, manifest_path=root / "plugin.yaml", manifest=manifest)


def test_resolve_load_order_respects_dependencies(tmp_path: Path) -> None:
    a = _pkg("a", [], tmp_path / "a")
    b = _pkg("b", ["a"], tmp_path / "b")
    c = _pkg("c", ["b"], tmp_path / "c")
    ordered = resolve_load_order([c, a, b])
    assert [p.name for p in ordered] == ["a", "b", "c"]


def test_resolve_load_order_detects_cycle(tmp_path: Path) -> None:
    a = _pkg("a", ["b"], tmp_path / "a")
    b = _pkg("b", ["a"], tmp_path / "b")
    with pytest.raises(PluginLoadError, match="circular"):
        resolve_load_order([a, b])


def test_resolve_load_order_missing_dependency(tmp_path: Path) -> None:
    a = _pkg("a", ["missing"], tmp_path / "a")
    with pytest.raises(PluginLoadError, match="missing"):
        resolve_load_order([a])


def test_discover_packages_from_modules() -> None:
    modules = Path(__file__).resolve().parents[1] / "modules"
    index = PluginLoader().discover_packages([modules])
    names = {p.name for p in index.packages}
    assert "daily" in names
    assert "reminder" in names
    ordered = index.ordered()
    assert {p.name for p in ordered} >= {"daily", "reminder"}


@pytest.mark.asyncio
async def test_runtime_loads_packages_in_order() -> None:
    runtime = AutomationRuntime.create()
    root = Path(__file__).resolve().parents[1]
    report = await runtime.plugins.load_from_paths_report([root / "modules"])
    assert any(p.metadata.name == "daily" for p in report.loaded)
    assert "daily.report" in runtime.registry.names()
