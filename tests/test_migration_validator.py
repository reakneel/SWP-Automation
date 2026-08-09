from pathlib import Path

from core.migration.inventory import MigrationCategory, build_inventory_item
from core.migration.validator import validate_item


def test_validator_accepts_inventory_with_entrypoint(tmp_path: Path) -> None:
    source = tmp_path / "legacy.py"
    source.write_text("def run():\n    return 1\n", encoding="utf-8")
    item = build_inventory_item(
        "run",
        "legacy.py",
        entrypoint="run",
        category=MigrationCategory.UTILITY,
    )

    result = validate_item(item, tmp_path)
    assert result.ready is True
    assert result.reasons == ()
