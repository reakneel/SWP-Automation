from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.migration.inventory import InventoryItem, MigrationStatus
from core.migration.validator import validate_item


@dataclass(frozen=True, slots=True)
class MigrationPlanItem:
    name: str
    source: str
    output: Path
    enabled: bool
    reasons: tuple[str, ...] = ()


def build_plan(
    items: list[InventoryItem],
    source_root: Path,
    output_root: Path,
) -> list[MigrationPlanItem]:
    plan: list[MigrationPlanItem] = []
    for item in items:
        result = validate_item(item, source_root)
        enabled = result.ready and item.status in {
            MigrationStatus.CLASSIFIED,
            MigrationStatus.WRAPPED,
        }
        plan.append(
            MigrationPlanItem(
                name=item.name,
                source=item.source,
                output=output_root / f"{item.name}.py",
                enabled=False,
                reasons=tuple(result.reasons) if not result.ready else (),
            )
        )
    return plan
