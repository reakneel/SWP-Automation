from __future__ import annotations

import importlib


class PluginImporter:
    """Import plugin classes from manifest entrypoints."""

    def load_class(
        self,
        module_name: str,
        class_name: str,
    ) -> type:
        module = importlib.import_module(module_name)
        return getattr(module, class_name)
