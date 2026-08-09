# Plugin Development Guide

Plugins are the unit of business integration. A plugin should package one coherent capability and expose one or more `Task` implementations.

## 1. Minimum contract

```python
from core.plugin.base import Plugin, PluginMetadata
from core.task.base import Task, TaskContext, TaskResult


class HelloTask(Task):
    name = "example.hello"
    description = "Run the example automation."

    async def run(self, context: TaskContext) -> TaskResult:
        return TaskResult.ok("hello", run_id=context.run_id)


class ExamplePlugin(Plugin):
    metadata = PluginMetadata(
        name="example",
        version="1.0.0",
        description="Example automation plugin",
        tags=["example"],
    )

    def tasks(self) -> list[Task]:
        return [HelloTask()]
```

## 2. Required rules

- `PluginMetadata.name` is stable and unique.
- Task names are globally unique and use `<plugin>.<action>` format.
- Tasks are async and must return `TaskResult`.
- Do not create your own scheduler, worker, retry loop, or database connection in a task.
- Use `TaskContext.run_id` for correlation and `context.metadata` for invocation metadata.
- External APIs belong behind a service/provider adapter.
- Secrets come from configuration/environment, never hard-coded source files.
- `startup()`/`shutdown()` are for lifecycle resources only; keep them idempotent.
- A plugin must be safe to load without executing a task.

## 3. Fast embedding an existing script

For an existing script, do not rewrite it first. Wrap it with a thin Task adapter:

```python
class LegacyTask(Task):
    name = "legacy.sync"

    async def run(self, context: TaskContext) -> TaskResult:
        result = await run_legacy_function()
        return TaskResult.ok("sync completed", result=result)
```

Then expose it through a plugin:

```python
class LegacyPlugin(Plugin):
    metadata = PluginMetadata(name="legacy", version="1.0.0")

    def tasks(self) -> list[Task]:
        return [LegacyTask()]
```

For a synchronous legacy function, run it through an executor rather than blocking the event loop.

## 4. Recommended package layout

```text
modules/<plugin>/
├── __init__.py
├── plugin.py
├── tasks.py
├── services.py
├── models.py
├── config.py
└── tests/
```

A very small plugin may start with only `plugin.py` and `tasks.py`.

## 5. Task naming

Use verbs for actions:

- `resource.update`
- `resource.sync`
- `daily.report`
- `reminder.trigger`

Avoid implementation names such as `resource.http_request`.

## 6. Execution model

```text
Plugin
  ↓
TaskRegistry
  ↓
TaskExecutor
  ↓
ExecutionStore
  ↓
EventBus
```

Scheduler, retry, timeout, concurrency, persistence, logging, and notifications are platform responsibilities. Plugins should only describe business behavior.

## 7. Plugin maturity levels

### Level 0 — Wrapper
Wrap an existing script with one Task.

### Level 1 — Structured plugin
Separate Task, service/provider, config, and tests.

### Level 2 — Production plugin
Add idempotency, retries through platform policy, structured results, health checks, and provider error handling.

### Level 3 — Reusable provider
Expose a stable provider interface so the same plugin can support multiple external systems.

## 8. Review checklist

Before merging a plugin:

- [ ] Unique plugin metadata name
- [ ] Unique `<plugin>.<action>` task names
- [ ] No blocking I/O on the event loop
- [ ] No custom scheduler/worker
- [ ] No secrets in code
- [ ] Idempotent where retries are possible
- [ ] TaskResult contains useful structured data
- [ ] Unit tests cover success and failure
- [ ] Existing M1/M3 runtime contracts are reused
