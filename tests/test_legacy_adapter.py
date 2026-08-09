import pytest

from core.plugin.legacy import LegacyFunctionTask
from core.task.base import TaskContext


def sync_update(value: int) -> dict[str, int]:
    return {"value": value + 1}


async def async_update(value: int) -> dict[str, int]:
    return {"value": value + 2}


@pytest.mark.asyncio
async def test_legacy_adapter_runs_sync_function() -> None:
    task = LegacyFunctionTask("legacy.sync", sync_update, value=1)
    result = await task.run(TaskContext(run_id="run-1"))
    assert result.success is True
    assert result.data["result"] == {"value": 2}


@pytest.mark.asyncio
async def test_legacy_adapter_awaits_async_function() -> None:
    task = LegacyFunctionTask("legacy.async", async_update, value=1)
    result = await task.run(TaskContext(run_id="run-2"))
    assert result.success is True
    assert result.data["result"] == {"value": 3}
