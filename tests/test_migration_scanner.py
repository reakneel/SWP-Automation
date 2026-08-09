from pathlib import Path

from core.migration.inventory import MigrationCategory
from core.migration.scanner import LegacyScanner


def test_scanner_detects_functions_dependencies_and_side_effects(tmp_path: Path) -> None:
    source = """
import httpx
import sqlite3

def refresh():
    with open('state.json', 'w') as fp:
        fp.write('ok')
"""
    path = tmp_path / "refresh.py"
    path.write_text(source, encoding="utf-8")

    items = LegacyScanner().scan_file(path, tmp_path)

    assert len(items) == 1
    item = items[0]
    assert item.name == "refresh"
    assert item.source == "refresh.py"
    assert item.dependencies == ["httpx", "sqlite3"]
    assert set(item.side_effects) == {"database", "filesystem", "http"}
    assert item.category is MigrationCategory.UNKNOWN


def test_scanner_skips_private_functions(tmp_path: Path) -> None:
    path = tmp_path / "module.py"
    path.write_text("def _internal():\n    pass\n\ndef public():\n    pass\n", encoding="utf-8")

    items = LegacyScanner().scan_file(path, tmp_path)
    assert [item.name for item in items] == ["public"]
