# Legacy Migration Manifest

M4.2 uses a small, repository-friendly manifest to inventory legacy scripts before they are wrapped or refactored.

## Status

- `discovered` — found during inventory
- `classified` — category and entrypoint are known
- `wrapped` — exposed through `LegacyFunctionTask`
- `migrated` — converted to a native plugin/task
- `retired` — intentionally removed

## Categories

- `resource` — resource/update/sync jobs
- `daily` — recurring maintenance or daily operations
- `reminder` — scheduled reminders and alerts
- `notification` — outbound notification adapters
- `provider` — external API/client integrations
- `cli` — command-line entrypoints
- `utility` — reusable helpers
- `dead` — unused or obsolete code

## Example

```yaml
version: 1
project: my-legacy-project
entries:
  - id: resource.update
    source: update.py:update_resources
    category: resource
    schedule: "0 */6 * * *"
    status: wrapped
    target: modules/resource
    blocking: true
    notes: "Wrap first; extract provider later."
```

## Migration rule

Inventory first, wrap second, refactor third. A legacy script must not gain its own scheduler, retry loop, database connection, or notification implementation when moved into SWP-Automation. Those concerns belong to the platform runtime or an adapter/provider plugin.
