from __future__ import annotations

from core.migration.inventory import InventoryItem, MigrationCategory


def classify_item(item: InventoryItem) -> InventoryItem:
    """Apply conservative category hints from names, paths, and side effects."""
    text = f"{item.name} {item.source}".lower()
    if item.category is not MigrationCategory.UNKNOWN:
        return item

    rules: tuple[tuple[MigrationCategory, tuple[str, ...]], ...] = (
        (MigrationCategory.REMINDER, ("remind", "reminder", "alarm")),
        (MigrationCategory.NOTIFICATION, ("notify", "notification", "alert")),
        (MigrationCategory.RESOURCE, ("resource", "download", "update", "sync", "feed")),
        (MigrationCategory.DAILY, ("daily", "cleanup", "backup", "report")),
        (MigrationCategory.PROVIDER, ("api", "client", "provider", "service")),
        (MigrationCategory.CLI, ("cli", "command")),
    )
    for category, keywords in rules:
        if any(keyword in text for keyword in keywords):
            item.category = category
            return item
    return item


def classify_items(items: list[InventoryItem]) -> list[InventoryItem]:
    return [classify_item(item) for item in items]
