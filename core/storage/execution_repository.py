from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.storage.models import ExecutionRow
from core.task.execution import ExecutionRecord, ExecutionStatus


class SqlExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, record: ExecutionRecord) -> None:
        row = ExecutionRow(
            run_id=record.run_id,
            task_name=record.task_name,
            status=record.status.value,
            started_at=record.started_at,
            finished_at=record.finished_at,
            message=record.message,
            data=record.data or {},
            error=record.error,
        )
        await self.session.merge(row)
        await self.session.commit()

    async def get(self, run_id: str) -> ExecutionRecord | None:
        row = await self.session.get(ExecutionRow, run_id)
        return self._to_record(row) if row else None

    async def list(self, limit: int = 100) -> list[ExecutionRecord]:
        result = await self.session.execute(
            select(ExecutionRow).order_by(ExecutionRow.started_at.desc()).limit(limit)
        )
        return [self._to_record(row) for row in result.scalars()]

    @staticmethod
    def _to_record(row: ExecutionRow) -> ExecutionRecord:
        return ExecutionRecord(
            run_id=row.run_id,
            task_name=row.task_name,
            status=ExecutionStatus(row.status),
            started_at=row.started_at,
            finished_at=row.finished_at,
            message=row.message or "",
            data=row.data or {},
            error=row.error,
        )
