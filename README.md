# SWP Automation

A modular Python automation platform for resource updates, daily jobs, reminders, monitoring, and external agent integrations.

> **Status:** M5.7 Distributed Runtime. Plugin platform accepted (M5.1–M5.6).

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
- Distributed task queue / multi-worker dispatch

### Business modules

- `modules/resource` — resource discovery, synchronization, and updates
- `modules/daily` — recurring daily operations and reports
- `modules/reminder` — scheduled reminders and triggers

### Infrastructure

- SQLAlchemy async persistence
- SQLite for development
- PostgreSQL for production
- Redis Streams for distributed events
- Redis distributed locks and task queue
- Scheduler / Worker runtime
- Docker Compose
- GitHub Actions CI
- structured JSON logging
- health / readiness checks

### Integrations

OpenClaw is an optional control plane and integration adapter. It must not be imported by `core/` or contain business logic.

## Plugin contract

**One capability = one Plugin. One executable action = one Task.**

See [docs/PLUGIN_GUIDE.md](docs/PLUGIN_GUIDE.md) and [docs/PLUGIN_TEMPLATE.md](docs/PLUGIN_TEMPLATE.md).

## Development

```bash
python -m pip install -e '.[dev,api,scheduler,storage,redis]'
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
worker    -> task execution (Redis queue when SWP_REDIS_URL is set)
scheduler -> scheduled job dispatch
postgres  -> durable execution data
redis     -> events / coordination / task queue
```

## Maturity roadmap

- **M1 — Core Runtime:** task/plugin/event/execution foundations — complete
- **M2 — Business Modules:** resource/daily/reminder — complete
- **M3 — Production Runtime:** persistence/scheduler/worker/Redis/Docker/OpenClaw — complete
- **M4 — Legacy Migration:** migrate existing standalone Python projects into plugins — complete
- **M5 — Plugin Platform:** contract, loader, runtime integration, execution safety — complete ([PROJECT_ACCEPTANCE](docs/PROJECT_ACCEPTANCE.md))
- **M5.6 — Plugin Package Layer:** versioned packages, dependencies, install paths — complete
- **M5.7 — Distributed Runtime:** shared task queue, multi-worker dispatch — complete ([docs](docs/M5_DISTRIBUTED_RUNTIME.md))
- **M5.8 — Enterprise Automation Platform** — next

## License

See repository license information.
