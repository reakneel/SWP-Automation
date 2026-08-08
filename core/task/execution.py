from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class ExecutionStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class ExecutionRecord:
    run_id: str
    task_name: str
    status: ExecutionStatus
    started_at: datetime
    finished_at: datetime | None = None
    message: str = ""
    data: dict[str, Any] | None = None
    error: str | None = None

    @property
    def duration_ms(self) -> float | None:
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds() * 1000

    def finish_success(self, message: str = "", data: dict[str, Any] | None = None) -> None:
        self.status = ExecutionStatus.SUCCESS
        self.message = message
        self.data = data or {}
        self.finished_at = datetime.now(timezone.utc)

    def finish_failure(self, error: str) -> None:
        self.status = ExecutionStatus.FAILED
        self.error = error
        self.finished_at = datetime.now(timezone.utc)
