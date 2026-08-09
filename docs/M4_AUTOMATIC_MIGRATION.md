# M4 Automatic Migration

The migration pipeline is intentionally **review-first**. Static analysis can discover and classify legacy code, but it must not execute arbitrary legacy code or silently enable generated tasks.

## Pipeline

```text
legacy repository
  -> AST scanner
  -> inventory
  -> validation
  -> migration plan
  -> JSON/report
  -> disabled adapter generation
  -> human review
  -> Plugin / Task
  -> runtime ownership
```

## CLI integration

```bash
swp migration scan ./legacy --output ./migration
swp migration validate ./migration/migration-inventory.json --source ./legacy
swp migration generate ./migration/migration-inventory.json --output ./plugins
swp migration migrate ./migration/migration-inventory.json --output ./plugins
```

`migrate` is a generation operation, not an execution operation. Generated adapters remain disabled until the legacy callable is explicitly wired and reviewed. Existing files are never overwritten.

## Safety rules

- Never import legacy modules during scanning, classification, or validation.
- Never execute discovered functions automatically.
- Never overwrite an existing generated adapter.
- Keep uncertain categories as `unknown`.
- Require review before enabling a generated task.
- Preserve original source, entrypoint, dependencies, and side effects in inventory.
- Keep scheduler, retry, timeout, persistence, and notifications in Automation Core.

## Completion gate

A task becomes `migrated` only after the generated adapter is wired to the real callable, tests pass, configuration is migrated, and the runtime owns execution policy.

## Ruff

The repository uses a 200-character Ruff line length to reduce formatting churn in migration tooling. CI runs `ruff check . --fix` before the final lint check; generated changes still require review.
