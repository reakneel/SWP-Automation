from __future__ import annotations

from typing import Any


async def uptime_check_batch(metadata: dict[str, Any]) -> dict[str, Any]:
    """Simulate or dry-run batch URL checks. Real HTTP can be added later."""
    urls = list(metadata.get("urls") or ["https://example.com"])
    dry_run = bool(metadata.get("dry_run", True))
    forced = metadata.get("uptime_results")
    checks = (
        forced
        if isinstance(forced, list)
        else [{"url": url, "status": 200, "ms": 1, "ok": True, "dry_run": dry_run} for url in urls]
    )
    ok = all(bool(c.get("ok", True)) for c in checks)
    return {"ok": ok, "checks": checks, "dry_run": dry_run}


async def web_watch_check(metadata: dict[str, Any]) -> dict[str, Any]:
    url = str(metadata.get("url") or "https://example.com")
    changed = bool(metadata.get("changed", False))
    content_hash = str(metadata.get("content_hash") or "sim-hash")
    previous_hash = str(metadata.get("previous_hash") or content_hash)
    if metadata.get("force_changed") is True:
        changed = True
        content_hash = f"{previous_hash}-next"
    return {
        "url": url,
        "changed": changed,
        "content_hash": content_hash,
        "previous_hash": previous_hash,
        "dry_run": bool(metadata.get("dry_run", True)),
    }


async def rss_poll(metadata: dict[str, Any]) -> dict[str, Any]:
    feed_url = str(metadata.get("feed_url") or "https://example.com/feed.xml")
    items = list(metadata.get("items") or [])
    if metadata.get("simulate_new_items"):
        items = list(items) + [{"title": "Simulated item", "link": "https://example.com/1"}]
    return {
        "feed_url": feed_url,
        "new_items": len(items),
        "items": items,
        "dry_run": bool(metadata.get("dry_run", True)),
    }


async def github_watch_release(metadata: dict[str, Any]) -> dict[str, Any]:
    repo = str(metadata.get("repo") or "reakneel/SWP-Automation")
    tag = metadata.get("tag")
    new_release = bool(metadata.get("new_release", False))
    if metadata.get("simulate_new_release") is True:
        new_release = True
        tag = str(tag or "v0.0.0-sim")
    return {
        "repo": repo,
        "new_release": new_release,
        "tag": tag,
        "dry_run": bool(metadata.get("dry_run", True)),
    }


def build_digest(step_results: dict[str, dict[str, Any]]) -> dict[str, Any]:
    highlights: list[str] = []
    failures: list[str] = []

    uptime = step_results.get("uptime.check_batch") or {}
    if uptime.get("ok") is False:
        failures.append("uptime: one or more checks failed")
    else:
        highlights.append("uptime: all checks ok")

    watch = step_results.get("web_watch.check") or {}
    if watch.get("changed"):
        highlights.append(f"web_watch: changed ({watch.get('url')})")
    else:
        highlights.append("web_watch: no change")

    rss = step_results.get("rss.poll") or {}
    n = int(rss.get("new_items") or 0)
    if n:
        highlights.append(f"rss: {n} new item(s)")
    else:
        highlights.append("rss: no new items")

    gh = step_results.get("github.watch_release") or {}
    if gh.get("new_release"):
        highlights.append(f"github: new release {gh.get('tag')}")
    else:
        highlights.append("github: no new release")

    needs_notify = bool(failures) or bool(watch.get("changed")) or n > 0 or bool(gh.get("new_release"))
    severity = "critical" if failures else ("attention" if needs_notify else "ok")
    return {
        "severity": severity,
        "needs_notify": needs_notify,
        "highlights": highlights,
        "failures": failures,
        "steps": {k: {"ok": True, "data": v} for k, v in step_results.items()},
    }


async def notify_send(metadata: dict[str, Any], digest: dict[str, Any]) -> dict[str, Any]:
    channel = str(metadata.get("channel") or "log")
    dry_run = bool(metadata.get("dry_run", True))
    body = str(metadata.get("body") or "; ".join(digest.get("highlights") or []))
    return {
        "channel": channel,
        "sent": not dry_run and bool(digest.get("needs_notify")),
        "skipped": dry_run or not digest.get("needs_notify"),
        "body": body,
        "dry_run": dry_run,
    }


async def heartbeat_ping(metadata: dict[str, Any]) -> dict[str, Any]:
    check_id = str(metadata.get("check_id") or "morning_pulse")
    return {
        "check_id": check_id,
        "ok": True,
        "workflow_id": metadata.get("workflow_id"),
    }
