from __future__ import annotations

import asyncio
import traceback
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from core.config.settings import get_settings
from core.events.bus import EventBus
from core.task.base import TaskContext
from core.task.execution import ExecutionRecord, ExecutionStatus
from core.task.registry import TaskRegistry
from core.task.store import ExecutionStore


class TaskCompletedEvent:
    def __init__(self, record: ExecutionRecord) -> None:
        self.record = record


class TaskExecutor:
    """Execute registered tasks and record their lifecycle."""

    def __init__(
        self,
        registry: TaskRegistry,
        store: ExecutionStore | None = None,
        event_bus: EventBus | None = None,
        *,
        timeout_seconds: float | None = None,
        metadata_max_keys: int | None = None,
        metadata_max_value_length: int | None = None,
    ) -> None:
        settings = get_settings()
        self.registry = registry
        self.store = store or ExecutionStore()
        self.event_bus = event_bus
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else settings.execution_timeout_seconds
        )
        self.metadata_max_keys = (
            metadata_max_keys if metadata_max_keys is not None else settings.metadata_max_keys
        )
        self.metadata_max_value_length = (
            metadata_max_value_length
            if metadata_max_value_length is not None
            else settings.metadata_max_value_length
        )

    def _validate_metadata(self, metadata: dict[str, Any] | None) -> dict[str, Any]:
        data = metadata or {}
        if not isinstance(data, dict):
            raise ValueError("metadata must be a dict")
        if len(data) > self.metadata_max_keys:
            raise ValueError(f"metadata exceeds max keys ({self.metadata_max_keys})")
        for key, value in data.items():
            if not isinstance(key, str):
                raise ValueError("metadata keys must be strings")
            text = value if isinstance(value, str) else repr(value)
            if len(text) > self.metadata_max_value_length:
                raise ValueError(
                    f"metadata value for {key!r} exceeds max length ({self.metadata_max_value_length})"
                )
        return data

    async def execute(
        self,
        task_name: str,
        metadata: dict | None = None,
        *,
        timeout_seconds: float | None = None,
    ) -> ExecutionRecord:
        if not task_name or not isinstance(task_name, str):
            raise ValueError("task_name must be a non-empty string")

        task = self.registry.get(task_name)
        run_id = str(uuid4())
        record = ExecutionRecord(
            run_id=run_id,
            task_name=task_name,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(UTC),
        )
        self.store.add(record)

        try:
            safe_metadata = self._validate_metadata(metadata)
        except ValueError as exc:
            record.finish_failure(str(exc))
            if self.event_bus is not None:
                await self.event_bus.publish(TaskCompletedEvent(record))
            return record

        context = TaskContext(run_id=run_id, metadata=safe_metadata)
        limit = self.timeout_seconds if timeout_seconds is None else timeout_seconds

        try:
            result = await asyncio.wait_for(task.run(context), timeout=limit)
            if result.success:
                record.finish_success(result.message, result.data)
            else:
                record.finish_failure(result.message or "task returned failure")
        except TimeoutError:
            record.finish_failure(f"task timed out after {limit}s")
        except Exception as exc:  # noqa: BLE001
            record.finish_failure(f"{exc}\n{traceback.format_exc()}")

        if self.event_bus is not None:
            await self.event_bus.publish(TaskCompletedEvent(record))
        return record
