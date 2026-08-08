from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.storage.models import ExecutionRow
from core.task.execution import ExecutionRecord


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
            data=record.data,
            error=record.error,
        )
        await self.session.merge(row)
        await self.session.commit()

    async def get(self, run_id: str) -> ExecutionRow | None:
        return await self.session.get(ExecutionRow, run_id)

    async def list(self, limit: int = 100) -> list[ExecutionRow]:
        result = await self.session.execute(
            select(ExecutionRow).order_by(ExecutionRow.started_at.desc()).limit(limit)
        )
        return list(result.scalars())
