# M4.3 Script Inventory

The migration inventory is the bridge between a legacy Python automation repository and the Automation Core.

## Normalized record

Each legacy unit should record:

- `name`: stable migration name
- `source`: original file/module
- `entrypoint`: callable or CLI entrypoint when known
- `category`: `resource`, `daily`, `reminder`, `notification`, `provider`, `cli`, `utility`, `dead`, or `unknown`
- `status`: `discovered`, `classified`, `wrapped`, `migrated`, or `retired`
- `schedule`: original cron/schedule if any
- `side_effects`: HTTP, filesystem, database, notification, subprocess, etc.
- `dependencies`: external packages/services
- `notes`: migration constraints

## Migration rule

Do not rewrite a legacy script during inventory. Record the existing behavior first, then wrap it with `LegacyFunctionTask` where possible. Move scheduling, retries, timeout, persistence, and notification into the platform runtime.

## Example

```python
from core.migration import MigrationCategory, build_inventory_item

item = build_inventory_item(
    "refresh-feed",
    "legacy/refresh.py",
    entrypoint="refresh",
    category=MigrationCategory.RESOURCE,
    schedule="0 * * * *",
    side_effects=["http", "filesystem"],
    dependencies=["httpx"],
)
```

## Definition of done

A migration unit is ready for M4.3 wrapping when its source, entrypoint, category, schedule, side effects, and dependencies are known. Unknown values should remain explicit rather than guessed.
