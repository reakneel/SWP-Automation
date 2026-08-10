from __future__ import annotations

import json
from pathlib import Path

from core.migration.pipeline import MigrationPipeline
from core.migration.cli import migrate_inventory, validate_inventory


def _write_legacy_project(root: Path) -> None:
    (root / "legacy_task.py").write_text(
        """
import httpx


def refresh_resource():
    return httpx.get("https://example.com")
""".strip()
        + "\n",
        encoding="utf-8",
    )


def test_scan_validate_generate_pipeline(tmp_path: Path) -> None:
    source = tmp_path / "legacy"
    output = tmp_path / "migration"
    plugins = tmp_path / "plugins"
    source.mkdir()
    _write_legacy_project(source)

    items = MigrationPipeline().export(source, output)
    assert items
    inventory = output / "migration-inventory.json"
    assert inventory.exists()

    payload = json.loads(inventory.read_text(encoding="utf-8"))
    assert payload
    assert payload[0]["source"].endswith("legacy_task.py")
    assert validate_inventory(inventory, source) == []

    generated = migrate_inventory(inventory, plugins)
    assert generated
    adapter = generated[0]
    text = adapter.read_text(encoding="utf-8")
    assert "LegacyFunctionTask" in text
    assert "NotImplementedError" in text

    compile(text, str(adapter), "exec")
