# M4 Legacy Migration

M4 migrates existing standalone Python scripts into the Automation Runtime without forcing a rewrite.

## Migration strategy

```text
Existing script
     |
     v
LegacyFunctionTask / thin adapter
     |
     v
Plugin
     |
     v
TaskRegistry -> TaskExecutor -> ExecutionStore/EventBus
```

### Phase 1 — Wrap

Keep mature business logic unchanged. Wrap a callable with `LegacyFunctionTask` or a small `Task` subclass.

```python
from core.plugin.legacy import LegacyFunctionTask

from old_project.update import update_resources

task = LegacyFunctionTask(
    name="legacy.update",
    function=update_resources,
)
```

For functions that need arguments, provide them as keyword arguments. For async functions the adapter awaits the returned coroutine.

### Phase 2 — Package

Create a plugin package:

```text
modules/<name>/
├── __init__.py
├── plugin.py
├── tasks.py
├── services.py      # optional
├── models.py        # optional
├── config.py        # optional
└── tests/
```

One capability should have one plugin; one executable action should have one namespaced task.

### Phase 3 — Refactor

Only after the wrapper is stable, extract external I/O into providers/services and move configuration behind the platform configuration boundary.

## Migration inventory

Before migrating a legacy repository, classify each script:

| Category | Examples | Target |
|---|---|---|
| Resource | scraping, update feeds, sync | `modules/resource` or new plugin |
| Daily | cleanup, reports, recurring jobs | `modules/daily` or new plugin |
| Reminder | timers, alerts, scheduled notices | `modules/reminder` or new plugin |
| Notification | email, webhook, chat delivery | notification adapter |
| Provider | API client, scraper, storage | service/provider |
| CLI | manual command | Task + CLI entry point |
| Utility | pure helper | keep as library/helper |
| Dead code | unused scripts | delete, do not migrate |

## Rules

- Do not copy an old scheduler or cron implementation into the plugin.
- Do not create a second database or execution history store.
- Do not block the event loop with synchronous network/file work; isolate blocking work with an executor or replace it with async I/O.
- Preserve idempotency where the old operation may be retried.
- Keep task names stable: `<plugin>.<action>`.
- Keep secrets out of source code.
- Add tests around the adapter before deep refactoring.

## Definition of done

A migrated script is complete when:

- it is reachable through a registered plugin/task;
- it uses platform execution, persistence, retry and scheduling;
- it has a deterministic task name;
- its old entry point is either delegated to the new task or removed;
- tests cover success and the primary failure path;
- no duplicate scheduler/worker/database infrastructure remains.
