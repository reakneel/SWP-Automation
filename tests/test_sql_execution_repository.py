from datetime import datetime, timezone

import pytest

from core.storage.execution_repository import SqlExecutionRepository
from core.task.execution import ExecutionRecord, ExecutionStatus


@pytest.mark.asyncio
async def test_sql_execution_repository_round_trip(session) -> None:
    repository = SqlExecutionRepository(session)
    record = ExecutionRecord(
        run_id="run-1",
        task_name="test.task",
        status=ExecutionStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
    )
    await repository.save(record)

    loaded = await repository.get("run-1")
    assert loaded is not None
    assert loaded.run_id == record.run_id
    assert loaded.task_name == record.task_name
    assert loaded.status == ExecutionStatus.RUNNING
