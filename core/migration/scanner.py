from __future__ import annotations

import ast
from pathlib import Path

from core.migration.inventory import InventoryItem, build_inventory_item


_HTTP_IMPORTS = {"requests", "httpx", "aiohttp", "urllib", "urllib3"}
_DB_IMPORTS = {"sqlalchemy", "psycopg", "asyncpg", "sqlite3", "pymysql", "redis"}
_NOTIFICATION_IMPORTS = {"telegram", "discord", "slack"}


class LegacyScanner:
    """Static AST scanner; never imports or executes the legacy project."""

    def scan_file(self, path: Path, root: Path | None = None) -> list[InventoryItem]:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        relative = str(path.relative_to(root or path.parent)) if root else str(path)
        imports = self._imports(tree)
        side_effects = self._side_effects(imports, tree)
        items: list[InventoryItem] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                items.append(
                    build_inventory_item(
                        node.name,
                        relative,
                        entrypoint=node.name,
                        side_effects=side_effects,
                        dependencies=sorted(imports),
                    )
                )
        return items

    def scan_directory(self, root: Path) -> list[InventoryItem]:
        items: list[InventoryItem] = []
        for path in sorted(root.rglob("*.py")):
            if any(part in {".venv", "venv", "__pycache__", ".git", "node_modules"} for part in path.parts):
                continue
            try:
                items.extend(self.scan_file(path, root))
            except (SyntaxError, UnicodeDecodeError):
                continue
        return items

    @staticmethod
    def _imports(tree: ast.AST) -> set[str]:
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        return imports

    @staticmethod
    def _side_effects(imports: set[str], tree: ast.AST) -> list[str]:
        effects: set[str] = set()
        if imports & _HTTP_IMPORTS:
            effects.add("http")
        if imports & _DB_IMPORTS:
            effects.add("database")
        if imports & _NOTIFICATION_IMPORTS:
            effects.add("notification")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"open", "print"}:
                    effects.add("filesystem" if node.func.id == "open" else "stdout")
                if node.func.id in {"system", "popen"}:
                    effects.add("subprocess")
        return sorted(effects)
