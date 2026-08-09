# M4 Automatic Migration

The migration pipeline is intentionally **review-first**. Static analysis can discover and classify legacy code, but it must not execute arbitrary legacy code or silently enable generated tasks.

## Pipeline

```text
legacy repository
  -> AST scanner
  -> inventory
  -> conservative classifier
  -> JSON/report
  -> adapter generator
  -> human review
  -> Plugin / Task
```

## CLI integration

The pipeline can be exposed by the project CLI as:

```bash
swp migration scan ./legacy --output ./migration
swp migration generate ./migration/migration-inventory.json --output ./plugins
```

Generated adapters are intentionally non-runnable until the legacy callable import is wired. Existing files are never overwritten.

## Safety rules

- Never import legacy modules during scanning.
- Never execute discovered functions automatically.
- Never overwrite an existing generated adapter.
- Keep uncertain categories as `unknown`.
- Require review before enabling a generated task.
- Preserve original source, entrypoint, dependencies, and side effects in inventory.

## Migration completion

A task becomes `migrated` only after the generated adapter has been wired to the real callable, tests pass, configuration is migrated, and the runtime owns scheduling/retry/timeout/persistence.
