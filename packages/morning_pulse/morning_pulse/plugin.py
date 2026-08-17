from __future__ import annotations

from core.plugin.base import Plugin, PluginMetadata
from core.task.base import Task, TaskContext, TaskResult
from packages.morning_pulse.morning_pulse import steps
from packages.morning_pulse.morning_pulse.orchestrator import run_morning_pulse


class _UptimeBatchTask(Task):
    name = "uptime.check_batch"
    description = "Batch URL uptime checks (dry-run capable)."

    async def run(self, context: TaskContext) -> TaskResult:
        data = await steps.uptime_check_batch(context.metadata)
        if not data.get("ok", True):
            return TaskResult.failure("uptime checks failed", **data)
        return TaskResult.ok("uptime checks completed", **data)


class _WebWatchTask(Task):
    name = "web_watch.check"
    description = "Check whether a watched URL content changed."

    async def run(self, context: TaskContext) -> TaskResult:
        data = await steps.web_watch_check(context.metadata)
        return TaskResult.ok("web watch completed", **data)


class _RssPollTask(Task):
    name = "rss.poll"
    description = "Poll an RSS/Atom feed for new items."

    async def run(self, context: TaskContext) -> TaskResult:
        data = await steps.rss_poll(context.metadata)
        return TaskResult.ok("rss poll completed", **data)


class _GithubWatchTask(Task):
    name = "github.watch_release"
    description = "Watch a GitHub repository for a new release."

    async def run(self, context: TaskContext) -> TaskResult:
        data = await steps.github_watch_release(context.metadata)
        return TaskResult.ok("github release watch completed", **data)


class _DigestTask(Task):
    name = "digest.build"
    description = "Build a digest from provided step_results metadata."

    async def run(self, context: TaskContext) -> TaskResult:
        raw = context.metadata.get("step_results") or {}
        if not isinstance(raw, dict):
            return TaskResult.failure("step_results must be a dict")
        data = steps.build_digest(raw)
        return TaskResult.ok("digest built", **data)


class _NotifyTask(Task):
    name = "notify.send"
    description = "Send a notification (dry-run by default)."

    async def run(self, context: TaskContext) -> TaskResult:
        digest = context.metadata.get("digest") or {
            "needs_notify": bool(context.metadata.get("needs_notify", False)),
            "highlights": list(context.metadata.get("highlights") or []),
        }
        data = await steps.notify_send(context.metadata, digest)
        return TaskResult.ok("notify completed", **data)


class _HeartbeatTask(Task):
    name = "heartbeat.ping"
    description = "Record a workflow heartbeat."

    async def run(self, context: TaskContext) -> TaskResult:
        data = await steps.heartbeat_ping(context.metadata)
        return TaskResult.ok("heartbeat recorded", **data)


class _MorningPulseRunTask(Task):
    name = "morning_pulse.run"
    description = "Orchestrate morning pulse: checks → digest → notify → heartbeat."

    async def run(self, context: TaskContext) -> TaskResult:
        data = await run_morning_pulse(context.metadata)
        severity = (data.get("digest") or {}).get("severity", "ok")
        if severity == "critical":
            return TaskResult.failure("morning pulse finished with failures", **data)
        return TaskResult.ok("morning pulse finished", **data)


class MorningPulsePlugin(Plugin):
    metadata = PluginMetadata(
        name="morning_pulse",
        version="0.1.0",
        description="Reference multi-step morning reliability and product-pulse workflow.",
        tags=["workflow", "uptime", "rss", "github", "digest"],
    )

    def tasks(self) -> list[Task]:
        return [
            _UptimeBatchTask(),
            _WebWatchTask(),
            _RssPollTask(),
            _GithubWatchTask(),
            _DigestTask(),
            _NotifyTask(),
            _HeartbeatTask(),
            _MorningPulseRunTask(),
        ]
