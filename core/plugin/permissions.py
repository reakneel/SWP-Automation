from __future__ import annotations

KNOWN_PERMISSIONS: frozenset[str] = frozenset(
    {
        "task.execute",
        "net.http",
        "fs.read",
        "fs.write",
        "notify",
    }
)

DEFAULT_PERMISSIONS: tuple[str, ...] = ("task.execute",)


def validate_permissions(permissions: list[str], *, strict: bool = False) -> list[str]:
    """Normalize and optionally reject unknown permission strings."""
    normalized = [p.strip() for p in permissions if p and p.strip()]
    if not normalized:
        return list(DEFAULT_PERMISSIONS)

    if strict:
        unknown = sorted({p for p in normalized if p not in KNOWN_PERMISSIONS})
        if unknown:
            from core.plugin.exceptions import PluginPermissionError

            raise PluginPermissionError(f"unknown permissions: {', '.join(unknown)}")
    return normalized


def is_module_allowed(module_name: str, prefixes: list[str]) -> bool:
    """Return True when module_name is under one of the allowed prefixes."""
    if not module_name or module_name.startswith(".") or ".." in module_name:
        return False
    return any(module_name == p.rstrip(".") or module_name.startswith(p if p.endswith(".") else f"{p}.") for p in prefixes)
