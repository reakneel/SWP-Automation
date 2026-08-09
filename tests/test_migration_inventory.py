from core.migration.inventory import (
    MigrationCategory,
    MigrationStatus,
    build_inventory_item,
)


def test_build_inventory_item_classifies_legacy_task() -> None:
    item = build_inventory_item(
        "refresh-feed",
        "legacy/refresh.py",
        entrypoint="refresh",
        category=MigrationCategory.RESOURCE,
        schedule="0 * * * *",
        side_effects=["http", "filesystem"],
        dependencies=["httpx"],
    )

    assert item.status is MigrationStatus.CLASSIFIED
    assert item.category is MigrationCategory.RESOURCE
    assert item.entrypoint == "refresh"
    assert item.schedule == "0 * * * *"


def test_unknown_item_stays_discovered() -> None:
    item = build_inventory_item("misc", "legacy/misc.py")
    assert item.status is MigrationStatus.DISCOVERED
    assert item.category is MigrationCategory.UNKNOWN
