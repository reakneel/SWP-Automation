"""Validate a package plugin directory without executing business logic."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from core.plugin.permissions import KNOWN_PERMISSIONS
from integrations.ai.context import repo_root

NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass
class CheckResult:
    ok: bool
    path: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: dict[str, str] = field(default_factory=dict)


def check_plugin_package(path: str | Path, *, root: Path | None = None) -> CheckResult:
    root = root or repo_root()
    pkg = Path(path)
    if not pkg.is_absolute():
        pkg = root / pkg
    result = CheckResult(ok=True, path=str(pkg))
    yaml_path = pkg / "plugin.yaml"
    if not yaml_path.is_file():
        result.ok = False
        result.errors.append("missing plugin.yaml")
        return result

    try:
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        result.ok = False
        result.errors.append(f"invalid yaml: {exc}")
        return result

    name = str(data.get("name") or "")
    result.info["name"] = name
    if not NAME_RE.match(name):
        result.errors.append(f"invalid name: {name!r}")

    entry = data.get("entrypoint") or {}
    module = str(entry.get("module") or "")
    cls = str(entry.get("class") or "")
    result.info["module"] = module
    result.info["class"] = cls
    if not module.startswith(f"packages.{name}."):
        result.errors.append(f"entrypoint.module should start with packages.{name}.")
    if not cls.endswith("Plugin"):
        result.warnings.append("entrypoint class usually ends with Plugin")

    perms = data.get("permissions") or []
    if not isinstance(perms, list):
        result.errors.append("permissions must be a list")
    else:
        unknown = sorted({str(p) for p in perms if str(p) not in KNOWN_PERMISSIONS})
        if unknown:
            result.errors.append(f"unknown permissions: {', '.join(unknown)}")

    expected_py = pkg / name / "plugin.py"
    if not expected_py.is_file():
        result.errors.append(f"missing {name}/plugin.py")
    else:
        try:
            tree = ast.parse(expected_py.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            result.errors.append(f"syntax error in plugin.py: {exc}")
        else:
            classes = [n.name for n in tree.body if isinstance(n, ast.ClassDef)]
            if cls and cls not in classes:
                result.errors.append(f"class {cls} not found in plugin.py (found: {classes})")

    result.ok = not result.errors
    return result
