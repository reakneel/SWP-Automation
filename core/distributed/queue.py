from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4


@dataclass(slots=True)
class TaskJob:
    """A unit of work shared between producers (API/scheduler) and workers."""

    task_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    job_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> TaskJob:
        return cls(
            job_id=str(payload.get("job_id") or uuid4()),
            task_name=str(payload["task_name"]),
            metadata=dict(payload.get("metadata") or {}),
            created_at=str(payload.get("created_at") or datetime.now(UTC).isoformat()),
        )


class TaskQueue(Protocol):
    async def enqueue(self, job: TaskJob) -> str: ...

    async def dequeue(self, timeout: float = 1.0) -> TaskJob | None: ...

    async def ack(self, job_id: str) -> None: ...

    async def size(self) -> int: ...


class InMemoryTaskQueue:
    """Process-local queue for tests and single-node development."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[TaskJob] = asyncio.Queue()
        self._pending: set[str] = set()

    async def enqueue(self, job: TaskJob) -> str:
        await self._queue.put(job)
        self._pending.add(job.job_id)
        return job.job_id

    async def dequeue(self, timeout: float = 1.0) -> TaskJob | None:
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except TimeoutError:
            return None

    async def ack(self, job_id: str) -> None:
        self._pending.discard(job_id)

    async def size(self) -> int:
        return self._queue.qsize()


class RedisTaskQueue:
    """Redis list-backed task queue for multi-worker dispatch."""

    def __init__(self, redis: Any, key: str = "automation:tasks") -> None:
        self.redis = redis
        self.key = key
        self.processing_key = f"{key}:processing"

    async def enqueue(self, job: TaskJob) -> str:
        await self.redis.rpush(self.key, json.dumps(job.to_payload(), default=str))
        return job.job_id

    async def dequeue(self, timeout: float = 1.0) -> TaskJob | None:
        # BLPOP returns (key, value) or None
        result = await self.redis.blpop(self.key, timeout=max(1, int(timeout)))
        if result is None:
            return None
        _, raw = result
        if isinstance(raw, bytes):
            raw = raw.decode()
        job = TaskJob.from_payload(json.loads(raw))
        await self.redis.hset(
            self.processing_key,
            job.job_id,
            raw if isinstance(raw, str) else json.dumps(job.to_payload()),
        )
        return job

    async def ack(self, job_id: str) -> None:
        await self.redis.hdel(self.processing_key, job_id)

    async def size(self) -> int:
        return int(await self.redis.llen(self.key))
