import pytest
from datetime import datetime, timedelta, timezone

from core.runtime import AutomationRuntime
from modules.daily.reminder_integration import install_m2_plugins


@pytest.mark.asyncio
async def test_daily_and_reminder_tasks_register() -> None:
    runtime = AutomationRuntime.create()
    await install_m2_plugins(runtime)

    assert {"daily.cleanup", "daily.report", "reminder.create", "reminder.cancel", "reminder.list", "reminder.trigger"} <= set(runtime.registry.names())

    result = await runtime.executor.execute("daily.cleanup")
    assert result.status.value == "success"

    result = await runtime.executor.execute(
        "reminder.create",
        {"title": "test", "due_at": (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()},
    )
    assert result.status.value == "success"
