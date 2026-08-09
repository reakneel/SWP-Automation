# SWP Automation

A modular Python automation platform for resource updates, daily jobs, reminders, monitoring, and external agent integrations.

> **Status:** M3 Production Runtime complete. M4 focuses on migrating existing standalone Python scripts into plugins.

## What this project is

SWP Automation turns a collection of unrelated Python scripts into one maintainable automation runtime:

```text
OpenClaw / Web / CLI
        |
        v
 Automation API
        |
        v
 Task Registry <---- Plugins
        |
        v
 Scheduler ---> Worker
        |          |
        |          +--> retry / timeout / concurrency
        |
        v
 AutomationRuntime
        |
   +----+---------+----------------+
   |              |                |
resource         daily          reminder
   |              |                |
   +--------------+----------------+
                  |
            Event Bus / Redis
                  |
        +---------+----------+
        |                    |
   PostgreSQL          Notifications
```

## Architecture layers

### Core

The core owns execution mechanics, not business logic.

- Task / TaskRegistry
- Plugin / PluginManager
- AutomationRuntime
- TaskExecutor
- ExecutionStore / Repository
- EventBus
- Scheduler boundary
- Worker lifecycle
- Notification boundary

### Business modules

- `modules/resource` — resource discovery, synchronization, and updates
- `modules/daily` — recurring daily operations and reports
- `modules/reminder` — scheduled reminders and triggers

### Infrastructure

- SQLAlchemy async persistence
- SQLite for development
- PostgreSQL for production
- Redis Streams for distributed events
- Redis distributed locks
- Scheduler / Worker runtime
- Docker Compose
- GitHub Actions CI
- structured JSON logging
- health / readiness checks

### Integrations

OpenClaw is an optional control plane and integration adapter. It must not be imported by `core/` or contain business logic.

## Plugin contract

**One capability = one Plugin. One executable action = one Task.**

A minimal plugin:

```python
from core.plugin.base import Plugin, PluginMetadata
from core.task.base import Task, TaskContext, TaskResult


class ExampleTask(Task):
    name = "example.run"
    description = "Run the example automation."

    async def run(self, context: TaskContext) -> TaskResult:
        result = await do_something()
        return TaskResult.ok("completed", result=result)


class ExamplePlugin(Plugin):
    metadata = PluginMetadata(
        name="example",
        version="1.0.0",
        description="Example automation plugin.",
    )

    def tasks(self) -> list[Task]:
        return [ExampleTask()]
```

Recommended layout:

```text
modules/example/
├── __init__.py
├── plugin.py
├── tasks.py
├── services.py
├── models.py
├── config.py
└── tests/
```

### Fast migration of an existing script

Do not rewrite a mature script first. Wrap it with a thin Task adapter:

```python
class LegacyUpdateTask(Task):
    name = "legacy.update"

    async def run(self, context: TaskContext) -> TaskResult:
        result = await asyncio.to_thread(old_update_function)
        return TaskResult.ok("legacy update completed", result=result)
```

Then register the task through a plugin. Scheduler, retry, timeout, persistence, events, and notifications remain owned by the platform.

See [`docs/PLUGIN_GUIDE.md`](docs/PLUGIN_GUIDE.md) and [`docs/PLUGIN_TEMPLATE.md`](docs/PLUGIN_TEMPLATE.md).

## Plugin rules

1. Plugins must not implement their own scheduler or worker.
2. Plugins must not write directly to the execution database.
3. Long-running synchronous work must be isolated from the event loop.
4. Configuration belongs to the plugin; secrets come from environment/config providers.
5. Tasks should be idempotent when possible.
6. Task names must be stable and namespaced, for example `resource.update`.
7. External providers belong behind provider/source interfaces.
8. Notifications should use the platform notification boundary.
9. OpenClaw integration belongs under `integrations/`, never `core/`.
10. Every plugin should have focused unit tests.

## Development

```bash
python -m pip install -e '.[dev,api,scheduler,storage]'
pytest
ruff check .
```

## Local infrastructure

```bash
docker compose up -d postgres redis
```

See [`docker/README.md`](docker/README.md) for the production-style stack.

## API

```bash
uvicorn apps.api.main:app --reload
```

Health check: `GET /health`

## Runtime services

The production Compose stack is split into:

```text
api       -> HTTP/API control plane
worker    -> task execution
scheduler -> scheduled job dispatch
postgres  -> durable execution data
redis     -> events / coordination
```

## Maturity roadmap

- **M1 — Core Runtime:** task/plugin/event/execution foundations — complete
- **M2 — Business Modules:** resource/daily/reminder — complete
- **M3 — Production Runtime:** persistence/scheduler/worker/Redis/Docker/OpenClaw — complete
- **M4 — Legacy Migration:** migrate existing standalone Python projects into plugins

## License

See repository license information.
