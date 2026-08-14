from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from core.plugin.exceptions import PluginConfigError, PluginLoadError, PluginPermissionError
from core.plugin.loader import PluginLoader
from core.plugin.permissions import is_module_allowed, validate_permissions
from core.plugin.state import PluginState
from core.runtime import AutomationRuntime
from core.task.base import Task, TaskContext, TaskResult
from core.task.execution import ExecutionStatus
from core.task.registry import TaskRegistry
from core.worker.executor import TaskExecutor


def test_module_allowlist() -> None:
    assert is_module_allowed("modules.daily.plugin", ["modules."])
    assert not is_module_allowed("os.path", ["modules."])
    assert not is_module_allowed("subprocess", ["modules."])
    assert not is_module_allowed("../evil", ["modules."])
    assert is_module_allowed("integrations.foo", ["modules.", "integrations."])


def test_validate_permissions_defaults_and_strict() -> None:
    assert validate_permissions([]) == ["task.execute"]
    assert validate_permissions(["net.http"]) == ["net.http"]
    with pytest.raises(PluginPermissionError):
        validate_permissions(["space.launch"], strict=True)


def test_loader_rejects_disallowed_entrypoint(tmp_path: Path) -> None:
    manifest = tmp_path / "plugin.yaml"
    manifest.write_text(
        "name: bad\nversion: 0.0.1\ncategory: test\nentrypoint:\n  module: os.path\n  class: join\n"
    )
    with pytest.raises(PluginLoadError, match="not allowed"):
        PluginLoader().parse_manifest(manifest)


def test_loader_strict_permissions(tmp_path: Path) -> None:
    manifest = tmp_path / "plugin.yaml"
    manifest.write_text(
        "name: weird\nversion: 0.0.1\ncategory: test\nentrypoint:\n  module: modules.daily.plugin\n"
        "  class: DailyPlugin\npermissions:\n  - space.launch\n"
    )
    with pytest.raises(PluginConfigError):
        PluginLoader(strict_permissions=True).parse_manifest(manifest)


@pytest.mark.asyncio
async def test_executor_timeout() -> None:
    class SlowTask(Task):
        name = "slow.run"
        description = "sleeps"

        async def run(self, context: TaskContext) -> TaskResult:
            await asyncio.sleep(5)
            return TaskResult.ok("done")

    registry = TaskRegistry()
    registry.register(SlowTask())
    executor = TaskExecutor(registry, timeout_seconds=0.05)
    record = await executor.execute("slow.run")
    assert record.status is ExecutionStatus.FAILED
    assert record.error is not None
    assert "timed out" in record.error


@pytest.mark.asyncio
async def test_executor_rejects_oversized_metadata() -> None:
    class EchoTask(Task):
        name = "echo.run"
        description = "echo"

        async def run(self, context: TaskContext) -> TaskResult:
            return TaskResult.ok("ok", **context.metadata)

    registry = TaskRegistry()
    registry.register(EchoTask())
    executor = TaskExecutor(registry, metadata_max_keys=2)
    record = await executor.execute("echo.run", {"a": 1, "b": 2, "c": 3})
    assert record.status is ExecutionStatus.FAILED
    assert record.error is not None
    assert "max keys" in record.error


@pytest.mark.asyncio
async def test_batch_load_isolates_failures(tmp_path: Path) -> None:
    good = tmp_path / "good"
    good.mkdir()
    (good / "plugin.yaml").write_text(
        "name: daily\nversion: 0.1.0\ncategory: business\nentrypoint:\n"
        "  module: modules.daily.plugin\n  class: DailyPlugin\npermissions:\n  - task.execute\n"
    )
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "plugin.yaml").write_text(
        "name: evil\nversion: 0.0.1\ncategory: test\nentrypoint:\n  module: os.path\n  class: join\n"
    )

    runtime = AutomationRuntime.create()
    report = await runtime.plugins.load_from_paths_report([tmp_path])

    assert any(p.metadata.name == "daily" for p in report.loaded)
    assert report.failed
    assert "daily.cleanup" in runtime.registry.names()
    entry = runtime.plugins.plugin_registry.get("daily")
    assert entry is not None
    assert entry.state is PluginState.INITIALIZED


@pytest.mark.asyncio
async def test_manual_load_still_works() -> None:
    from modules.daily.plugin import DailyPlugin

    runtime = AutomationRuntime.create()
    await runtime.plugins.load(DailyPlugin())
    assert "daily.cleanup" in runtime.registry.names()
