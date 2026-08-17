from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from packages.morning_pulse.morning_pulse import steps


async def run_morning_pulse(metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Parent workflow: sequential checks → digest → optional notify → heartbeat."""
    meta = dict(metadata or {})
    workflow_id = str(
        meta.get("workflow_id") or f"morning_pulse:{datetime.now(UTC).date()}:{uuid4().hex[:8]}"
    )
    meta.setdefault("workflow_id", workflow_id)
    meta.setdefault("dry_run", True)

    step_results: dict[str, dict[str, Any]] = {}
    step_results["uptime.check_batch"] = await steps.uptime_check_batch(meta)
    step_results["web_watch.check"] = await steps.web_watch_check(meta)
    step_results["rss.poll"] = await steps.rss_poll(meta)
    step_results["github.watch_release"] = await steps.github_watch_release(meta)

    digest = steps.build_digest(step_results)
    notify = await steps.notify_send(meta, digest)
    heartbeat = await steps.heartbeat_ping(meta)

    return {
        "workflow_id": workflow_id,
        "finished": True,
        "digest": digest,
        "notify": notify,
        "heartbeat": heartbeat,
        "steps": step_results,
    }
