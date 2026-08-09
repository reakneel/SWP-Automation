from pathlib import Path

from core.migration.inventory import MigrationCategory, build_inventory_item
from core.migration.plan import build_plan


def test_plan_keeps_generated_tasks_disabled(tmp_path: Path) -> None:
    source = tmp_path / "legacy"
    source.mkdir()
    (source / "refresh.py").write_text("def refresh():\n    return True\n", encoding="utf-8")

    item = build_inventory_item(
        "refresh-feed",
        "refresh.py",
        entrypoint="refresh",
        category=MigrationCategory.RESOURCE,
    )
    plan = build_plan([item], source, tmp_path / "plugins")

    assert len(plan) == 1
    assert plan[0].enabled is False
    assert plan[0].output.name == "refresh_feed.py"
