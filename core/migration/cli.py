from __future__ import annotations

import json
from pathlib import Path

from core.migration.inventory import InventoryItem, MigrationCategory, MigrationStatus
from core.migration.pipeline import MigrationPipeline
from core.migration.validator import validate_item


def load_inventory(path: Path) -> list[InventoryItem]:
    raw_items = json.loads(path.read_text(encoding="utf-8"))
    return [
        InventoryItem(
            name=item["name"],
            source=item["source"],
            entrypoint=item.get("entrypoint"),
            category=MigrationCategory(item.get("category", "unknown")),
            status=MigrationStatus(item.get("status", "discovered")),
            schedule=item.get("schedule"),
            side_effects=item.get("side_effects", []),
            dependencies=item.get("dependencies", []),
            notes=item.get("notes", ""),
            metadata=item.get("metadata", {}),
        )
        for item in raw_items
    ]


def validate_inventory(inventory: Path, source_root: Path) -> list[str]:
    errors: list[str] = []
    for item in load_inventory(inventory):
        result = validate_item(item, source_root)
        if not result.ready:
            errors.append(f"{item.name}: {'; '.join(result.reasons)}")
    return errors


def migrate_inventory(inventory: Path, output: Path) -> list[Path]:
    return MigrationPipeline().generate_adapters(load_inventory(inventory), output)
