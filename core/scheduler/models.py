from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Job:
    id: str
    task_name: str
    trigger: str = "interval"
    seconds: int = 60
    enabled: bool = True
    max_instances: int = 1
    coalesce: bool = True
    misfire_grace_time: int = 60
    metadata: dict[str, Any] = field(default_factory=dict)
    next_run_at: datetime | None = None
