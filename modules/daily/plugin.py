from __future__ import annotations

from core.plugin.base import Plugin, PluginMetadata
from core.task.base import Task
from modules.daily.tasks import DailyTask, default_cleanup, default_report


class DailyPlugin(Plugin):
    metadata = PluginMetadata(
        name="daily", version="0.1.0", description="Daily operational automation.", tags=["daily"],
    )

    def tasks(self) -> list[Task]:
        return [
            DailyTask("daily.cleanup", "Run daily cleanup operations.", default_cleanup),
            DailyTask("daily.report", "Generate the daily report.", default_report),
        ]
