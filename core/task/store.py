from __future__ import annotations

from collections import deque
from threading import Lock

from core.task.execution import ExecutionRecord


class ExecutionStore:
    """Small in-memory execution store; replaceable by SQL/Redis later."""

    def __init__(self, max_records: int = 1000) -> None:
        self._records: deque[ExecutionRecord] = deque(maxlen=max_records)
        self._lock = Lock()

    def add(self, record: ExecutionRecord) -> None:
        with self._lock:
            self._records.append(record)

    def list(self, limit: int = 100) -> list[ExecutionRecord]:
        with self._lock:
            return list(reversed(self._records))[:limit]

    def get(self, run_id: str) -> ExecutionRecord | None:
        with self._lock:
            return next((r for r in self._records if r.run_id == run_id), None)
