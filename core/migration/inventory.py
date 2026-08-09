from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class MigrationCategory(StrEnum):
    RESOURCE = "resource"
    DAILY = "daily"
    REMINDER = "reminder"
    NOTIFICATION = "notification"
    PROVIDER = "provider"
    CLI = "cli"
    UTILITY = "utility"
    DEAD = "dead"
    UNKNOWN = "unknown"


class MigrationStatus(StrEnum):
    DISCOVERED = "discovered"
    CLASSIFIED = "classified"
    WRAPPED = "wrapped"
    MIGRATED = "migrated"
    RETIRED = "retired"


@dataclass(slots=True)
class InventoryItem:
    name: str
    source: str
    entrypoint: str | None = None
    category: MigrationCategory = MigrationCategory.UNKNOWN
    status: MigrationStatus = MigrationStatus.DISCOVERED
    schedule: str | None = None
    side_effects: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def build_inventory_item(
    name: str,
    source: str,
    *,
    entrypoint: str | None = None,
    category: MigrationCategory = MigrationCategory.UNKNOWN,
    schedule: str | None = None,
    side_effects: list[str] | None = None,
    dependencies: list[str] | None = None,
    notes: str = "",
    metadata: dict[str, Any] | None = None,
) -> InventoryItem:
    """Create a normalized inventory record for a legacy automation unit."""
    return InventoryItem(
        name=name,
        source=source,
        entrypoint=entrypoint,
        category=category,
        status=MigrationStatus.CLASSIFIED if category != MigrationCategory.UNKNOWN else MigrationStatus.DISCOVERED,
        schedule=schedule,
        side_effects=list(side_effects or []),
        dependencies=list(dependencies or []),
        notes=notes,
        metadata=dict(metadata or {}),
    )
