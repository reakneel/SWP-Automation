# SWP Automation

A modular Python automation platform for resource updates, daily jobs, reminders, monitoring, and external agent integrations.

## Architecture

```text
OpenClaw / Web / CLI
        |
        v
   Automation API
        |
        v
   Task Registry
        |
        v
      Worker
        |
  +-----+-----+----------------+
  |           |                |
resource     daily          reminder
  |           |                |
  +-----------+----------------+
              |
          Event Bus
              |
     Notification / Storage
```

## Core principles

- Business modules are isolated from scheduling and transport concerns.
- Tasks expose a stable async execution contract.
- Plugins register tasks without changing the core runtime.
- Scheduler implementations are replaceable.
- Notification channels are replaceable.
- OpenClaw is an optional control plane; it is not the business logic layer.

## Development

```bash
python -m pip install -e '.[dev,api,scheduler,storage]'
pytest
ruff check .
```

## API

```bash
uvicorn apps.api.main:app --reload
```

Health check: `GET /health`
