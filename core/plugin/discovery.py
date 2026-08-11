from __future__ import annotations

from pathlib import Path


PLUGIN_MANIFEST = "plugin.yaml"


class PluginDiscovery:
    """Discover plugin manifests from configured locations."""

    def discover(
        self,
        paths: list[Path],
    ) -> list[Path]:
        manifests: list[Path] = []

        for path in paths:
            if not path.exists():
                continue

            for manifest in path.rglob(PLUGIN_MANIFEST):
                manifests.append(manifest)

        return manifests
