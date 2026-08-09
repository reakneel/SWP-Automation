# M4.9 Migration CLI

The migration CLI provides a reviewable end-to-end workflow without importing or executing legacy code.

```text
scan -> inventory -> validate -> generate/migrate -> human review
```

## Commands

```bash
automation migration scan ./legacy --output ./migration
automation migration validate ./migration/migration-inventory.json --source ./legacy
automation migration generate ./migration/migration-inventory.json --output ./plugins
automation migration migrate ./migration/migration-inventory.json --output ./plugins
```

`generate` and `migrate` create disabled adapters. They never execute legacy callables. A generated adapter must be reviewed and wired to the original callable before it can be enabled.

## Safety boundary

The scanner uses AST analysis and the migration commands operate on inventory metadata. They do not import arbitrary legacy modules, execute functions, or install legacy dependencies.

## CI

Ruff is configured with a 200-character line length. CI runs `ruff check . --fix` before the final lint pass and then executes the test suite.
