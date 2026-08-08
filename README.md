# SWP Automation

A modular Python automation platform for scheduled jobs, reminders, resource updates, monitoring, and external integrations.

## Architecture

```text
CLI / API / OpenClaw
        |
        v
   Task Registry
        |
   Automation Core
   |    |      |
 Event Scheduler Worker
   |    |      |
   +----+------+----> Modules / Integrations
```

The core deliberately keeps business modules independent. OpenClaw is intended to be an optional command layer rather than the owner of business logic.

## Initial modules

- `resource`: resource update and synchronization tasks
- `daily`: routine tasks
- `reminder`: reminders and notifications
- `monitoring`: health and change monitoring

## Development

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Unix: source .venv/bin/activate
pip install -e '.[all]'
pytest
ruff check .
```

## CLI

```bash
automation task list
automation task run example.hello
```

## Design principles

1. Deterministic business logic stays in Python modules.
2. Tasks are independently executable and observable.
3. Scheduling is separated from task implementation.
4. Events are used for loose coupling between modules.
5. External channels are integrations, not business logic.
6. OpenClaw can call the API/CLI without becoming a hard dependency.
