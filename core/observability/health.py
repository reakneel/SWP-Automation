from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class HealthStatus:
    status: str
    checks: dict[str, str]

    def as_dict(self) -> dict[str, Any]:
        return {"status": self.status, "checks": self.checks}


def health_status(*, database: str = "ok", redis: str = "ok") -> HealthStatus:
    checks = {"database": database, "redis": redis}
    overall = "ok" if all(value == "ok" for value in checks.values()) else "degraded"
    return HealthStatus(overall, checks)
