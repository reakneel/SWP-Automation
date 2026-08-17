from __future__ import annotations

import pytest

from core.runtime import AutomationRuntime
from core.task.execution import ExecutionStatus
from packages.morning_pulse.morning_pulse.orchestrator import run_morning_pulse
from packages.morning_pulse.morning_pulse.plugin import MorningPulsePlugin


@pytest.mark.asyncio
async def test_orchestrator_quiet_morning() -> None:
    result = await run_morning_pulse({"dry_run": True})
    assert result["finished"] is True
    assert result["heartbeat"]["ok"] is True
    assert result["digest"]["severity"] == "ok"
    assert result["digest"]["needs_notify"] is False
    assert result["notify"]["skipped"] is True


@pytest.mark.asyncio
async def test_orchestrator_attention_on_new_release() -> None:
    result = await run_morning_pulse(
        {
            "dry_run": True,
            "simulate_new_release": True,
            "tag": "v1.2.3",
        }
    )
    assert result["digest"]["severity"] == "attention"
    assert result["digest"]["needs_notify"] is True
    assert any("v1.2.3" in h for h in result["digest"]["highlights"])


@pytest.mark.asyncio
async def test_plugin_registers_and_run_task() -> None:
    runtime = AutomationRuntime.create()
    await runtime.plugins.load(MorningPulsePlugin())
    record = await runtime.executor.execute(
        "morning_pulse.run",
        {"dry_run": True, "simulate_new_items": True},
    )
    assert record.status is ExecutionStatus.SUCCESS
    assert record.data is not None
    assert record.data.get("finished") is True
    assert record.data.get("digest", {}).get("needs_notify") is True


@pytest.mark.asyncio
async def test_step_task_uptime() -> None:
    runtime = AutomationRuntime.create()
    await runtime.plugins.load(MorningPulsePlugin())
    record = await runtime.executor.execute(
        "uptime.check_batch",
        {"urls": ["https://a.example", "https://b.example"], "dry_run": True},
    )
    assert record.status is ExecutionStatus.SUCCESS
    assert record.data is not None
    assert record.data.get("ok") is True
    assert len(record.data.get("checks") or []) == 2
