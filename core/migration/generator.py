from __future__ import annotations

import re
from pathlib import Path

from core.migration.inventory import InventoryItem


def safe_module_name(value: str) -> str:
    """Return a stable Python module name for generated migration adapters."""
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    return value or "legacy_task"


def generate_task(item: InventoryItem, output_dir: Path) -> Path:
    """Generate a reviewable adapter, never overwrite an existing file."""
    if not item.entrypoint:
        raise ValueError(f"Cannot generate adapter without entrypoint: {item.name}")
    module_name = safe_module_name(item.name)
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f"{module_name}.py"
    if destination.exists():
        raise FileExistsError(destination)

    source = item.source.replace("\\", "/")
    source_module = source[:-3].replace("/", ".")
    content = "\n".join(
        [
            '"""Generated reviewable adapter; wire the legacy callable before enabling."""',
            "",
            "from core.plugin.legacy import LegacyFunctionTask",
            "",
            "",
            f"# TODO: from {source_module} import {item.entrypoint}",
            "",
            "",
            "def build_task() -> LegacyFunctionTask:",
            "    raise NotImplementedError(",
            f'        "Wire {item.entrypoint} from {source} before enabling this task"',
            "    )",
            "",
        ]
    )
    destination.write_text(content, encoding="utf-8")
    return destination
