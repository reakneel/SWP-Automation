from pathlib import Path

from core.migration.generator import generate_task
from core.migration.inventory import MigrationCategory, build_inventory_item


def test_generator_creates_reviewable_adapter(tmp_path: Path) -> None:
    item = build_inventory_item(
        "refresh-feed",
        "legacy/refresh_feed.py",
        entrypoint="refresh_feed",
        category=MigrationCategory.RESOURCE,
    )
    generated = generate_task(item, tmp_path)
    content = generated.read_text(encoding="utf-8")
    assert "LegacyFunctionTask" in content
    assert "NotImplementedError" in content
