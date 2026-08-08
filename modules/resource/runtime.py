from __future__ import annotations

from core.plugin.manager import PluginManager
from core.runtime import AutomationRuntime
from modules.resource.plugin import ResourcePlugin
from modules.resource.services import ResourceSource


async def install_resource_plugin(runtime: AutomationRuntime, source: ResourceSource) -> ResourcePlugin:
    """Install resource tasks into an existing application runtime."""
    plugin = ResourcePlugin(source)
    manager = PluginManager(runtime.registry)
    await manager.load(plugin)
    return plugin
