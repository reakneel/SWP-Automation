# Plugin AI Contract

Strict rules for any LLM or scaffold tool that generates SWP plugins.
Output must be reviewable package files under `packages/<name>/`.

## Required layout

```text
packages/<name>/
  plugin.yaml
  <name>/
    __init__.py
    plugin.py
```

- Package directory name: lowercase, digits, underscores only (`[a-z][a-z0-9_]*`).
- Import prefix: `packages.<name>.<name>.plugin`.
- Entrypoint class: `PascalCase` ending with `Plugin`.

## plugin.yaml

```yaml
name: <name>
version: 0.1.0
category: business
entrypoint:
  module: packages.<name>.<name>.plugin
  class: <Name>Plugin
permissions:
  - task.execute
dependencies: []
```

Allowed permissions only: `task.execute`, `net.http`, `fs.read`, `fs.write`, `notify`.

## Python rules

- Tasks subclass `Task`, expose `name` as `<plugin>.<action>`, async `run(self, context) -> TaskResult`.
- Plugin subclasses `Plugin` with `metadata: PluginMetadata` and `tasks() -> list[Task]`.
- No scheduler, worker, or DB engine inside the plugin.
- Secrets only from metadata/env — never hard-code.
- Prefer `TaskResult.ok` / `TaskResult.failure`.
- Network I/O only if `net.http` is declared; default dry-run safe behavior when practical.

## Output format (LLM)

Reply with one or more file blocks only (no prose outside blocks):

```text
### FILE: packages/<name>/plugin.yaml
<content>

### FILE: packages/<name>/<name>/__init__.py
<content>

### FILE: packages/<name>/<name>/plugin.py
<content>
```

## Forbidden

- Writing outside `packages/<name>/`
- Auto-enabling production side effects without dry-run metadata
- Inventing unknown permissions
- Putting LLM API calls inside `Task.run`
