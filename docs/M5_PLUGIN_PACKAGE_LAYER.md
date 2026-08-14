# M5.6 Plugin Package Layer

Versioned plugin packages with dependency ordering and install paths.

## Package layout

A package is any directory containing `plugin.yaml`:

```text
modules/daily/plugin.yaml     # in-tree
packages/my_tool/plugin.yaml  # external install path
```

## Manifest fields

| Field | Required | Notes |
|-------|----------|-------|
| `name` | yes | Unique plugin id |
| `version` | yes | Package version string |
| `category` | yes | e.g. business |
| `entrypoint.module` / `class` | yes | Must be under allowed prefixes |
| `permissions` | no | Defaults to `task.execute` |
| `dependencies` | no | List of other plugin **names** |

## Dependency resolution

`PluginLoader.discover_packages` → `PackageIndex.ordered()` performs a topological
sort. Missing dependencies or cycles raise `PluginLoadError` and fail the package
index step (recorded in `PluginLoadReport.failed`).

## Settings

| Env | Default |
|-----|---------|
| `SWP_PLUGIN_PATHS` | `["modules", "packages"]` |
| `SWP_PLUGIN_MODULE_PREFIXES` | `["modules.", "packages."]` |

## API

```python
from pathlib import Path
from core.runtime import AutomationRuntime

runtime = AutomationRuntime.create()
report = await runtime.plugins.load_from_paths_report([Path("modules"), Path("packages")])
```
