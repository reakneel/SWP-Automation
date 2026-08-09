from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.migration.inventory import InventoryItem


def inventory_to_dict(items: list[InventoryItem]) -> list[dict[str, Any]]:
    return [
        {
            "name": item.name,
            "source": item.source,
            "entrypoint": item.entrypoint,
            "category": item.category.value,
            "status": item.status.value,
            "schedule": item.schedule,
            "side_effects": item.side_effects,
            "dependencies": item.dependencies,
            "notes": item.notes,
            "metadata": item.metadata,
        }
        for item in items
    ]


def write_inventory(items: list[InventoryItem], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(inventory_to_dict(items), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def render_report(items: list[InventoryItem]) -> str:
    lines = ["# Legacy Migration Report", "", f"Total items: {len(items)}", ""]
    for item in items:
        lines.extend(
            [
                f"## {item.name}",
                f"- Source: `{item.source}`",
                f"- Entrypoint: `{item.entrypoint or 'unknown'}`",
                f"- Category: `{item.category.value}`",
                f"- Status: `{item.status.value}`",
                f"- Schedule: `{item.schedule or 'none'}`",
                f"- Side effects: {', '.join(item.side_effects) or 'none'}",
                f"- Dependencies: {', '.join(item.dependencies) or 'none'}",
                "",
            ]
        )
    return "\n".join(lines)
