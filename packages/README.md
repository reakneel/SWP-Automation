# Plugin packages

Drop third-party or standalone plugin packages here. Each package is a directory
containing `plugin.yaml` and Python modules importable under the `packages.` prefix
(or another prefix listed in `SWP_PLUGIN_MODULE_PREFIXES`).

Example:

```text
packages/
  my_tool/
    plugin.yaml
    my_tool/
      __init__.py
      plugin.py
```

Dependencies are declared in `plugin.yaml` as plugin names and are loaded in
topological order by the package layer (M5.6).
