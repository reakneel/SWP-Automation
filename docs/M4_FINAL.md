# M4 Automatic Migration — Final Contract

M4 provides a safe, reviewable migration pipeline for legacy Python automation.

## End-to-end flow

`scan -> inventory -> validate -> plan -> generate -> review -> wire -> test -> enable`

## Safety boundary

The scanner uses AST analysis and never imports or executes legacy source. Generated adapters are disabled by default and contain an explicit wiring step. Automatic migration may discover structure and generate boilerplate, but it must not silently execute unknown legacy code or change business behavior.

## CI contract

- Ruff `line-length` remains capped at 200.
- `ruff format .` runs before linting.
- `ruff check . --fix` may apply safe automatic fixes.
- A clean `ruff check .` is still required.
- The full pytest suite must pass.

## Definition of done

A legacy project is considered migrated only after its generated adapter has been reviewed, its callable has been wired, tests pass, and the task is explicitly enabled.
