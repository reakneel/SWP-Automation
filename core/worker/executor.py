from __future__ import annotations

from datetime import datetime, timezone
import traceback
from uuid import uuid4

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
    ) -> None:
        self.registry = registry
        self.store = store or ExecutionStore()
        self.event_bus = event_bus

    async def execute(self, task_name: str, metadata: dict | None = None) -> ExecutionRecord:
        task = self.registry.get(task_name)
        run_id = str(uuid4())
        record = ExecutionRecord(
            run_id=run_id,
            task_name=task_name,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        self.store.add(record)
        context = TaskContext(run_id=run_id, metadata=metadata or {})

        try:
            result = await task.run(context)
            if result.success:
                record.finish_success(result.message, result.data)
            else:
                record.finish_failure(result.message or "task returned failure")
        except Exception as exc:  # noqa: BLE001
            record.finish_failure(f"{exc}\n{traceback.format_exc()}")

        if self.event_bus is not None:
            await self.event_bus.publish(TaskCompletedEvent(record))
        return record
