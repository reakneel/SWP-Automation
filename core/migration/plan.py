from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.migration.generator import safe_module_name
from core.migration.inventory import InventoryItem
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
        plan.append(
            MigrationPlanItem(
                name=item.name,
                source=item.source,
                output=output_root / f"{safe_module_name(item.name)}.py",
                enabled=False,
                reasons=tuple(result.reasons) if not result.ready else (),
            )
        )
    return plan
