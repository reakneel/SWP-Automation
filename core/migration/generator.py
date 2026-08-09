from __future__ import annotations

import re
from pathlib import Path

from core.migration.inventory import InventoryItem


def _safe_identifier(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    return value or "legacy_task"


def generate_task(item: InventoryItem, output_dir: Path) -> Path:
    """Generate a reviewable adapter, never overwrite an existing file."""
    if not item.entrypoint:
        raise ValueError(f"Cannot generate adapter without entrypoint: {item.name}")
    module_name = _safe_identifier(item.name)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{module_name}.py"
    if destination.exists():
        raise FileExistsError(destination)

    source = item.source.replace("\\", "/")
    content = f'''from pathlib import Path\n\nfrom core.plugin.legacy import LegacyFunctionTask\n\n\n# TODO: import the legacy callable from the source project.\n# from {source[:-3].replace('/', '.')} import {item.entrypoint}\n\n\ndef build_task() -> LegacyFunctionTask:\n    raise NotImplementedError(\n        "Wire {item.entrypoint} from {source} before enabling this task"\n    )\n'''
    destination.write_text(content, encoding="utf-8")
    return destination
