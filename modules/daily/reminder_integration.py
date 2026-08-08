from __future__ import annotations

from core.runtime import AutomationRuntime
from core.plugin.manager import PluginManager
from modules.daily.plugin import DailyPlugin
from modules.reminder.plugin import ReminderPlugin


async def install_m2_plugins(runtime: AutomationRuntime) -> None:
    """Install the generic daily and reminder modules into a runtime."""
    manager = PluginManager(runtime.registry)
    await manager.load(DailyPlugin())
    await manager.load(ReminderPlugin())
