from __future__ import annotations

import pytest

from core.runtime import AutomationRuntime
from packages.bili_live_rec.bili_live_rec.plugin import BiliLiveRecPlugin
from packages.bili_live_rec.bili_live_rec.room import parse_room_input
from packages.bili_live_rec.bili_live_rec.wbi import fake_buvid3


def test_parse_room_input() -> None:
    assert parse_room_input("6") == "6"
    assert parse_room_input("https://live.bilibili.com/7734200") == "7734200"


def test_fake_buvid3_shape() -> None:
    b = fake_buvid3()
    assert b.endswith("infoc")
    assert len(b) > 20


@pytest.mark.asyncio
async def test_plugin_registers_tasks() -> None:
    runtime = AutomationRuntime.create()
    await runtime.plugins.load(BiliLiveRecPlugin())
    names = set(runtime.registry.names())
    assert "bili.room_check" in names
    assert "bili.stream_url" in names
    assert "bili.record_segment" in names


@pytest.mark.asyncio
async def test_room_check_requires_room() -> None:
    runtime = AutomationRuntime.create()
    await runtime.plugins.load(BiliLiveRecPlugin())
    record = await runtime.executor.execute("bili.room_check", {})
    assert record.status.value == "failed"
