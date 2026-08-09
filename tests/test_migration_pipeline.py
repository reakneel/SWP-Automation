from pathlib import Path

from core.migration.inventory import MigrationCategory
from core.migration.pipeline import MigrationPipeline


def test_pipeline_exports_and_generates(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "update_resource.py").write_text(
        "def update_resource():\n    return True\n", encoding="utf-8"
    )

    output = tmp_path / "out"
    pipeline = MigrationPipeline()
    items = pipeline.export(legacy, output)

    assert items[0].category is MigrationCategory.RESOURCE
    assert (output / "migration-inventory.json").exists()
    assert (output / "migration-report.md").exists()

    generated = pipeline.generate_adapters(items, output / "plugins")
    assert len(generated) == 1
    assert generated[0].exists()
