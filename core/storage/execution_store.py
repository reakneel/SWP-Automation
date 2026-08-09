from __future__ import annotations

from typing import Protocol

from core.task.execution import ExecutionRecord


class ExecutionRepository(Protocol):
    async def save(self, record: ExecutionRecord) -> None: ...
    async def get(self, run_id: str) -> ExecutionRecord | None: ...
    async def list(self, limit: int = 100) -> list[ExecutionRecord]: ...


class PersistentExecutionStore:
    """Runtime-facing store backed by a persistence repository."""

    def __init__(self, repository: ExecutionRepository) -> None:
        self.repository = repository

    async def add(self, record: ExecutionRecord) -> None:
        await self.repository.save(record)

    async def update(self, record: ExecutionRecord) -> None:
        await self.repository.save(record)

    async def get(self, run_id: str) -> ExecutionRecord | None:
        return await self.repository.get(run_id)

    async def list(self, limit: int = 100) -> list[ExecutionRecord]:
        return await self.repository.list(limit)
