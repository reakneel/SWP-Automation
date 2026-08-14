from __future__ import annotations

from pathlib import Path

import pytest

from core.plugin.exceptions import PluginConfigError, PluginLoadError
from core.plugin.loader import PluginLoader
from core.plugin.state import PluginState
from core.runtime import AutomationRuntime


@pytest.mark.asyncio
async def test_runtime_loads_plugins_from_modules_path() -> None:
    runtime = AutomationRuntime.create()
    modules = Path(__file__).resolve().parents[1] / "modules"

    loaded = await runtime.load_plugins([modules])

    names = {plugin.metadata.name for plugin in loaded}
    assert "daily" in names
    assert "reminder" in names
    assert "daily.cleanup" in runtime.registry.names()
    assert "daily.report" in runtime.registry.names()
    assert "reminder.create" in runtime.registry.names()

    entry = runtime.plugins.plugin_registry.get("daily")
    assert entry is not None
    assert entry.state == PluginState.INITIALIZED


@pytest.mark.asyncio
async def test_runtime_can_execute_loaded_plugin_task() -> None:
    runtime = AutomationRuntime.create()
    modules = Path(__file__).resolve().parents[1] / "modules"
    await runtime.load_plugins([modules])

    record = await runtime.executor.execute("daily.report")
    assert record.status.value == "success"


def test_loader_rejects_invalid_manifest(tmp_path: Path) -> None:
    bad = tmp_path / "plugin.yaml"
    bad.write_text("name: only\n")
    with pytest.raises(PluginConfigError):
        PluginLoader().parse_manifest(bad)


def test_loader_rejects_missing_entrypoint_module(tmp_path: Path) -> None:
    manifest = tmp_path / "plugin.yaml"
    manifest.write_text(
        "name: ghost\nversion: 0.0.1\ncategory: test\nentrypoint:\n  module: does.not.exist\n  class: Ghost\n"
    )
    with pytest.raises(PluginLoadError):
        PluginLoader().load_manifest(manifest)


@pytest.mark.asyncio
async def test_manual_load_still_works() -> None:
    from modules.daily.plugin import DailyPlugin

    runtime = AutomationRuntime.create()
    await runtime.plugins.load(DailyPlugin())
    assert "daily.cleanup" in runtime.registry.names()
