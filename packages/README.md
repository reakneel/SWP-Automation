# Plugin packages

Drop third-party or standalone plugin packages here. Each package is a directory
containing `plugin.yaml` and Python modules importable under the `packages.` prefix
(or another prefix listed in `SWP_PLUGIN_MODULE_PREFIXES`).

## Reference workflow

| Package | Description |
|---------|-------------|
| [`morning_pulse`](morning_pulse/) | Multi-step morning reliability + product pulse (see [WORKFLOW_MORNING_PULSE](../docs/WORKFLOW_MORNING_PULSE.md)) |

Example layout:

```text
packages/
  morning_pulse/
    plugin.yaml
    morning_pulse/
      __init__.py
      plugin.py
      steps.py
      orchestrator.py
```

Dependencies are declared in `plugin.yaml` as plugin names and are loaded in
topological order by the package layer (M5.6).
