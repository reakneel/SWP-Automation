"""Assemble documentation context for plugin authoring."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DOC_FILES = (
    "docs/PLUGIN_AI_CONTRACT.md",
    "docs/PLUGIN_TEMPLATE.md",
    "docs/PLUGIN_GUIDE.md",
)


def repo_root() -> Path:
    return ROOT


def list_plugin_docs() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for rel in DOC_FILES:
        path = ROOT / rel
        items.append(
            {
                "path": rel,
                "exists": str(path.is_file()),
                "bytes": str(path.stat().st_size if path.is_file() else 0),
            }
        )
    return items


def load_doc_pack(*, max_chars: int = 24000) -> str:
    parts: list[str] = []
    total = 0
    for rel in DOC_FILES:
        path = ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        chunk = f"\n\n===== {rel} =====\n{text}"
        if total + len(chunk) > max_chars:
            remain = max_chars - total
            if remain > 200:
                parts.append(chunk[:remain] + "\n...[truncated]...")
            break
        parts.append(chunk)
        total += len(chunk)
    return "".join(parts).strip()
