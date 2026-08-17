from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import requests

from core.plugin.base import Plugin, PluginMetadata
from core.task.base import Task, TaskContext, TaskResult
from packages.bili_live_rec.bili_live_rec.recorder import record_once, sanitize_filename
from packages.bili_live_rec.bili_live_rec.room import BiliRoomClient, QN_NAME


def _session_client(metadata: dict) -> BiliRoomClient:
    session = requests.Session()
    cookie = str(metadata.get("cookie") or "")
    return BiliRoomClient(session, cookie=cookie)


class _RoomCheckTask(Task):
    name = "bili.room_check"
    description = "Check Bilibili live room status (live / title / uid)."

    async def run(self, context: TaskContext) -> TaskResult:
        room_ref = str(context.metadata.get("room") or context.metadata.get("rooms") or "")
        if not room_ref:
            return TaskResult.failure("metadata.room is required")
        client = _session_client(context.metadata)
        try:
            state = client.get_room_info(room_ref)
        except Exception as exc:
            return TaskResult.failure(f"room_check failed: {exc}")
        status = {0: "offline", 1: "live", 2: "carousel"}.get(state.live_status, "unknown")
        return TaskResult.ok(
            "room checked",
            room_id=state.room_id,
            short_id=state.short_id,
            anchor_uid=state.anchor_uid,
            title=state.title,
            live_status=state.live_status,
            status=status,
        )


class _StreamUrlTask(Task):
    name = "bili.stream_url"
    description = "Resolve anonymous/login stream URL for a live room."

    async def run(self, context: TaskContext) -> TaskResult:
        room_ref = str(context.metadata.get("room") or "")
        if not room_ref:
            return TaskResult.failure("metadata.room is required")
        qn = int(context.metadata.get("qn") or 10000)
        client = _session_client(context.metadata)
        try:
            state = client.get_room_info(room_ref)
            if state.live_status != 1:
                return TaskResult.failure(
                    "room not live",
                    room_id=state.room_id,
                    live_status=state.live_status,
                    title=state.title,
                )
            stream = client.resolve_stream(state, qn=qn)
        except Exception as exc:
            return TaskResult.failure(f"stream_url failed: {exc}")
        return TaskResult.ok(
            "stream resolved",
            room_id=state.room_id,
            title=state.title,
            **stream,
            qn_table=QN_NAME,
        )


class _RecordSegmentTask(Task):
    name = "bili.record_segment"
    description = (
        "Record a bounded live segment with asyncio ffmpeg "
        "(stoppable; avoids blocking subprocess.run)."
    )

    async def run(self, context: TaskContext) -> TaskResult:
        room_ref = str(context.metadata.get("room") or "")
        if not room_ref:
            return TaskResult.failure("metadata.room is required")
        qn = int(context.metadata.get("qn") or 10000)
        fmt = str(context.metadata.get("format") or "flv")
        if fmt not in {"flv", "mp4", "ts"}:
            return TaskResult.failure("format must be flv|mp4|ts")
        max_seconds = float(context.metadata.get("max_seconds") or 60)
        max_seconds = max(5.0, min(max_seconds, 600.0))
        out_dir = Path(str(context.metadata.get("output") or "downloads"))
        dry_run = bool(context.metadata.get("dry_run", False))

        client = _session_client(context.metadata)
        try:
            state = client.get_room_info(room_ref)
            if state.live_status != 1:
                return TaskResult.failure("room not live", room_id=state.room_id, title=state.title)
            stream = client.resolve_stream(state, qn=qn)
        except Exception as exc:
            return TaskResult.failure(f"resolve failed: {exc}")

        if dry_run:
            return TaskResult.ok(
                "dry_run: would record",
                room_id=state.room_id,
                title=state.title,
                stream=stream,
                max_seconds=max_seconds,
            )

        base = sanitize_filename(f"{state.room_id}_{state.title}")
        stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        out = out_dir / f"{base}_{stamp}.{fmt}"
        try:
            result = await record_once(stream["url"], out, fmt=fmt, max_seconds=max_seconds)
        except Exception as exc:
            return TaskResult.failure(f"record failed: {exc}", room_id=state.room_id, stream=stream)

        if not result.get("ok"):
            return TaskResult.failure(
                "record produced empty file",
                room_id=state.room_id,
                stream=stream,
                **result,
            )
        return TaskResult.ok(
            "segment recorded",
            room_id=state.room_id,
            title=state.title,
            stream=stream,
            **result,
        )


class BiliLiveRecPlugin(Plugin):
    metadata = PluginMetadata(
        name="bili_live_rec",
        version="0.1.0",
        description="Bilibili live room check, stream resolve, bounded segment record.",
        tags=["bilibili", "live", "record"],
    )

    def tasks(self) -> list[Task]:
        return [_RoomCheckTask(), _StreamUrlTask(), _RecordSegmentTask()]
