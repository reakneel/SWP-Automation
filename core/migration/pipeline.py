from __future__ import annotations

from pathlib import Path

from core.migration.classifier import classify_items
from core.migration.generator import generate_task
from core.migration.inventory import InventoryItem
from core.migration.scanner import LegacyScanner
from core.migration.serializer import render_report, write_inventory


class MigrationPipeline:
    def __init__(self, scanner: LegacyScanner | None = None) -> None:
        self.scanner = scanner or LegacyScanner()

    def scan(self, root: Path) -> list[InventoryItem]:
        return classify_items(self.scanner.scan_directory(root))

    def export(self, root: Path, output_dir: Path) -> list[InventoryItem]:
        items = self.scan(root)
        write_inventory(items, output_dir / "migration-inventory.json")
        (output_dir / "migration-report.md").write_text(
            render_report(items), encoding="utf-8"
        )
        return items

    def generate_adapters(
        self, items: list[InventoryItem], output_dir: Path
    ) -> list[Path]:
        generated: list[Path] = []
        for item in items:
            if item.entrypoint and item.category.value != "dead":
                generated.append(generate_task(item, output_dir))
        return generated
