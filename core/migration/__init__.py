"""Legacy migration inventory and adapter utilities."""

from core.migration.inventory import (
    InventoryItem,
    MigrationCategory,
    MigrationStatus,
    build_inventory_item,
)

__all__ = [
    "InventoryItem",
    "MigrationCategory",
    "MigrationStatus",
    "build_inventory_item",
]
