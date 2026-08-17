#!/usr/bin/env python3
"""CLI adapter for agent skills — same core as SWP plugin tasks."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="bili-live skill tool runner")
    parser.add_argument(
        "tool",
        choices=["room_check", "stream_url", "record_segment"],
    )
    parser.add_argument("--room", required=True)
    parser.add_argument("--qn", type=int, default=10000)
    parser.add_argument("--cookie", default="")
    parser.add_argument("--max-seconds", type=float, default=60.0)
    parser.add_argument("--format", default="flv", choices=["flv", "mp4", "ts"])
    parser.add_argument("--output", default="downloads")
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument(
        "--require-ai-key",
        action="store_true",
        help="Exit 2 if SWP_AI_API_KEY is not set (agent-only mode)",
    )
    args = parser.parse_args()

    if args.require_ai_key:
        from integrations.ai.gate import ai_enabled

        if not ai_enabled():
            print(json.dumps({"ok": False, "error": "SWP_AI_API_KEY not set; use plugin path offline"}))
            return 2

    meta = {
        "room": args.room,
        "qn": args.qn,
        "cookie": args.cookie,
        "max_seconds": args.max_seconds,
        "format": args.format,
        "output": args.output,
        "dry_run": args.dry_run,
    }

    async def _run() -> dict:
        from core.runtime import AutomationRuntime
        from packages.bili_live_rec.bili_live_rec.plugin import BiliLiveRecPlugin

        runtime = AutomationRuntime.create()
        await runtime.plugins.load(BiliLiveRecPlugin())
        name = {
            "room_check": "bili.room_check",
            "stream_url": "bili.stream_url",
            "record_segment": "bili.record_segment",
        }[args.tool]
        record = await runtime.executor.execute(name, meta)
        return {
            "ok": record.status.value == "success",
            "status": record.status.value,
            "message": record.message,
            "data": record.data,
            "error": record.error,
            "path": "plugin",
        }

    result = asyncio.run(_run())
    print(json.dumps(result, ensure_ascii=False, default=str))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
