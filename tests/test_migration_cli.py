import json
from pathlib import Path

from core.migration.cli import load_inventory, validate_inventory
from core.migration.inventory import MigrationCategory


def test_load_inventory(tmp_path: Path) -> None:
    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        json.dumps(
            [
                {
                    "name": "refresh",
                    "source": "refresh.py",
                    "entrypoint": "refresh",
                    "category": "resource",
                    "status": "classified",
                }
            ]
        ),
        encoding="utf-8",
    )
    items = load_inventory(inventory)
    assert len(items) == 1
    assert items[0].category is MigrationCategory.RESOURCE


def test_validate_inventory_reports_missing_source(tmp_path: Path) -> None:
    inventory = tmp_path / "inventory.json"
    inventory.write_text(
        json.dumps(
            [
                {
                    "name": "refresh",
                    "source": "missing.py",
                    "entrypoint": "refresh",
                    "category": "resource",
                    "status": "classified",
                }
            ]
        ),
        encoding="utf-8",
    )
    errors = validate_inventory(inventory, tmp_path)
    assert errors == ["refresh: source file does not exist"]
