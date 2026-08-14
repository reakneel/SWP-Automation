# SWP Automation

A modular Python automation platform for resource updates, daily jobs, reminders, monitoring, and external agent integrations.

> **Status:** M5.8 Enterprise Automation Platform complete (M1–M5.8).

## What this project is

SWP Automation turns a collection of unrelated Python scripts into one maintainable automation runtime:

```text
OpenClaw / Web / CLI
        |
        v
 Automation API  (+ auth / tenant / rate limit / audit)
        |
        v
 Task Registry <---- Plugins / Packages
        |
        v
 Scheduler ---> Worker (distributed queue)
        |
        v
 AutomationRuntime
```

## Architecture layers

### Core

- Task / TaskRegistry / TaskExecutor
- Plugin / PluginManager / Package layer
- AutomationRuntime
- Distributed task queue
- Enterprise control plane (tenant, auth, audit, rate limit)

### Business modules

- `modules/resource`, `modules/daily`, `modules/reminder`

### Infrastructure

- PostgreSQL / SQLite, Redis, Docker Compose, GitHub Actions CI

## Development

```bash
python -m pip install -e '.[dev,api,scheduler,storage,redis]'
pytest
ruff check .
```

## API

```bash
uvicorn apps.api.main:app --reload
```

- Health: `GET /health`
- Readiness: `GET /ready`
- Admin: `GET /api/v1/admin/status` (API key when `SWP_API_KEYS` set)

## Maturity roadmap

- **M1 — Core Runtime** — complete
- **M2 — Business Modules** — complete
- **M3 — Production Runtime** — complete
- **M4 — Legacy Migration** — complete
- **M5 — Plugin Platform** — complete ([PROJECT_ACCEPTANCE](docs/PROJECT_ACCEPTANCE.md))
- **M5.6 — Plugin Package Layer** — complete
- **M5.7 — Distributed Runtime** — complete ([docs](docs/M5_DISTRIBUTED_RUNTIME.md))
- **M5.8 — Enterprise Automation Platform** — complete ([docs](docs/M5_ENTERPRISE_PLATFORM.md))

## License

See repository license information.
