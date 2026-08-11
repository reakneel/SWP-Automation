from pathlib import Path

from core.plugin.discovery import PluginDiscovery


def test_discovery_finds_manifest(tmp_path: Path):
    plugin = tmp_path / "example"
    plugin.mkdir()
    manifest = plugin / "plugin.yaml"
    manifest.write_text("name: example")

    result = PluginDiscovery().discover([tmp_path])

    assert manifest in result
