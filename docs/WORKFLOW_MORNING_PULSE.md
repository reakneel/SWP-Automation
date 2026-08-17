# Workflow blueprint: Morning Pulse

Reference multi-plugin workflow for SWP-Automation. Demonstrates how the platform
**finishes** a multi-step daily automation using existing M1–M5.8 capabilities.

## Scenario

Weekday morning reliability + product pulse:

1. Batch uptime checks on critical URLs
2. Website content change check
3. RSS/Atom feed poll for new items
4. GitHub release watch
5. Digest (severity + `needs_notify`)
6. Optional notify (dry-run by default)
7. Heartbeat close-out

## Package

| Path | Role |
|------|------|
| `packages/morning_pulse/` | Reference workflow plugin |
| Task `morning_pulse.run` | Parent orchestrator (recommended entry) |
| Step tasks | `uptime.check_batch`, `web_watch.check`, `rss.poll`, `github.watch_release`, `digest.build`, `notify.send`, `heartbeat.ping` |

## How SWP finishes the workflow

```text
Scheduler / API
      |
      |  TaskJob(task_name="morning_pulse.run", metadata={...})
      v
Redis queue (optional) → DistributedWorker → Worker → TaskExecutor
      |
      v
morning_pulse.run
  → uptime → web_watch → rss → github
  → digest.build (in-process)
  → notify.send (if needs_notify; dry_run default)
  → heartbeat.ping
      |
      v
ExecutionRecord + (API) AuditLog
```

**Finished when:** `morning_pulse.run` returns with `data.finished=true` and
`data.heartbeat.ok=true`. Critical uptime failures yield `TaskResult.failure`
with full step payload for inspection.

## Metadata (orchestrator)

| Key | Default | Meaning |
|-----|---------|---------|
| `workflow_id` | auto | Correlation id |
| `dry_run` | `true` | No external side effects |
| `urls` | `[https://example.com]` | Uptime targets |
| `url` | example.com | Web watch target |
| `feed_url` | example feed | RSS target |
| `repo` | `reakneel/SWP-Automation` | GitHub repo |
| `simulate_new_items` | false | Test helper |
| `simulate_new_release` | false | Test helper |
| `force_changed` | false | Test helper |
| `channel` | `log` | Notify channel label |

## Orchestration modes

| Mode | Support in this PR |
|------|--------------------|
| **B. Parent task** `morning_pulse.run` | Implemented |
| **A. Time-staged cron** (separate jobs) | Documented; use step task names |
| **C. Queue fan-out** | Documented; enqueue step tasks with shared `workflow_id` |

## Scheduler sketch

```text
Job morning_pulse @ 0 9 * * 1-5
  → enqueue morning_pulse.run
    metadata: { dry_run: false, urls: [...], repo: "org/app", channel: "ntfy" }
```

## Out of scope (later)

- Real HTTP/RSS/GitHub API clients (replace step stubs)
- Playwright / full changedetection.io
- Durable DAG engine

## Tests

`tests/test_morning_pulse_workflow.py` — orchestrator quiet path + attention path.
