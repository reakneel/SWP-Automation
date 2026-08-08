import pytest

from core.runtime import AutomationRuntime
from core.task.base import Task, TaskContext, TaskResult


class SuccessfulTask(Task):
    name = "test.success"
    description = "test task"

    async def run(self, context: TaskContext) -> TaskResult:
        return TaskResult(success=True, message="ok", data={"run_id": context.run_id})


class FailingTask(Task):
    name = "test.failure"
    description = "failing test task"

    async def run(self, context: TaskContext) -> TaskResult:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_runtime_records_success() -> None:
    runtime = AutomationRuntime.create()
    runtime.registry.register(SuccessfulTask())

    record = await runtime.executor.execute("test.success")

    assert record.status.value == "success"
    assert record.finished_at is not None
    assert record.duration_ms is not None
    assert runtime.executions.get(record.run_id) is record


@pytest.mark.asyncio
async def test_runtime_records_failure() -> None:
    runtime = AutomationRuntime.create()
    runtime.registry.register(FailingTask())

    record = await runtime.executor.execute("test.failure")

    assert record.status.value == "failed"
    assert "boom" in (record.error or "")
