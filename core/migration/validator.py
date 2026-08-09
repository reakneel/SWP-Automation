from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.migration.inventory import InventoryItem, MigrationCategory


@dataclass(slots=True, frozen=True)
class MigrationValidation:
    item: InventoryItem
    ready: bool
    reasons: tuple[str, ...]


def validate_item(item: InventoryItem, source_root: Path) -> MigrationValidation:
    reasons: list[str] = []
    source = source_root / item.source
    if not source.is_file():
        reasons.append("source file does not exist")
    if not item.entrypoint:
        reasons.append("entrypoint is missing")
    if item.category is MigrationCategory.UNKNOWN:
        reasons.append("category is unknown")
    return MigrationValidation(item, not reasons, tuple(reasons))
