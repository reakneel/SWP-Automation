import pytest

from core.runtime import AutomationRuntime
from modules.resource.models import Resource
from modules.resource.runtime import install_resource_plugin
from modules.resource.testing import StaticResourceSource


@pytest.mark.asyncio
async def test_resource_plugin_registers_tasks() -> None:
    runtime = AutomationRuntime.create()
    source = StaticResourceSource([Resource(id="1", title="demo", source="test")])

    await install_resource_plugin(runtime, source)

    assert "resource.update" in runtime.registry.names()
    assert "resource.sync" in runtime.registry.names()

    record = await runtime.executor.execute("resource.update")
    assert record.status.value == "success"
    assert record.data["created"] == 1

    record = await runtime.executor.execute("resource.update")
    assert record.status.value == "success"
    assert record.data["created"] == 0
