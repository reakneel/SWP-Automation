from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Job:
    id: str
    task_name: str
    trigger: str
    enabled: bool = True
    next_run_at: datetime | None = None
