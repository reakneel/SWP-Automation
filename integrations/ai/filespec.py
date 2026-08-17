"""Parse and apply ### FILE: blocks from scaffold output."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

FILE_BLOCK = re.compile(
    r"^### FILE:\s*(\S+)\s*$",
    re.MULTILINE,
)


@dataclass(slots=True)
class FileSpec:
    path: str
    content: str


def parse_file_blocks(text: str) -> list[FileSpec]:
    matches = list(FILE_BLOCK.finditer(text))
    if not matches:
        return []
    files: list[FileSpec] = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip("\n")
        if body.startswith("```"):
            lines = body.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            body = "\n".join(lines).strip("\n")
        path = match.group(1).strip()
        files.append(
            FileSpec(
                path=path,
                content=body + ("\n" if body and not body.endswith("\n") else ""),
            )
        )
    return files


def validate_package_paths(files: list[FileSpec], *, plugin_name: str) -> list[str]:
    errors: list[str] = []
    prefix = f"packages/{plugin_name}/"
    for f in files:
        p = f.path.replace("\\", "/")
        if not p.startswith(prefix):
            errors.append(f"path outside package: {f.path}")
        if ".." in p.split("/"):
            errors.append(f"invalid path: {f.path}")
    return errors


def apply_files(files: list[FileSpec], *, root: Path, dry_run: bool = True) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for f in files:
        target = root / f.path
        action = "would_write" if dry_run else "written"
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f.content, encoding="utf-8")
        results.append({"path": f.path, "action": action, "bytes": str(len(f.content.encode()))})
    return results
