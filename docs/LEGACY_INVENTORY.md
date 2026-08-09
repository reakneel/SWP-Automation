# Legacy Inventory Checklist

Use this checklist when importing an existing Python project.

## 1. Discover

- [ ] Python modules/scripts
- [ ] CLI entrypoints
- [ ] cron/systemd/task scheduler definitions
- [ ] environment variables and config files
- [ ] database access
- [ ] external API clients
- [ ] notification integrations
- [ ] generated files/cache

## 2. Classify

| Category | Typical examples | Target |
|---|---|---|
| resource | scraper, updater, sync | Resource Plugin |
| daily | cleanup, report, maintenance | Daily Plugin |
| reminder | alert, scheduled notice | Reminder Plugin |
| notification | Telegram/email/webhook | Notification Adapter |
| provider | Bilibili/GitHub/HTTP client | Provider |
| cli | command entrypoint | Task |
| utility | pure reusable helper | Service/Utility |
| dead | unused code | Retire |

## 3. Capture each entrypoint

Record the source file/function, inputs, side effects, schedule, blocking behavior, dependencies, and desired target plugin.

## 4. Migration order

1. Wrap unchanged code with `LegacyFunctionTask`.
2. Move scheduling to the platform scheduler.
3. Move retries/timeouts to the worker runtime.
4. Move notifications behind adapters.
5. Extract providers/services only after the task is stable.
6. Replace the wrapper with a native `Task` when migration is complete.

## 5. Acceptance criteria

A migrated capability must be runnable through the platform runtime, observable through execution records/events, and independently testable without depending on a legacy scheduler or process-global state.
