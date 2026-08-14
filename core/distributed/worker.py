from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from core.distributed.queue import TaskJob, TaskQueue
from core.task.execution import ExecutionRecord
from core.worker.runtime import Worker


@dataclass(slots=True)
class DistributedWorkerConfig:
    worker_id: str = "worker-1"
    poll_timeout: float = 1.0
    lock_ttl_seconds: int = 60
    use_task_lock: bool = True


class DistributedWorker:
    """Claim jobs from a shared queue and execute them via the local Worker."""

    def __init__(
        self,
        queue: TaskQueue,
        worker: Worker,
        *,
        lock: Any | None = None,
        config: DistributedWorkerConfig | None = None,
    ) -> None:
        self.queue = queue
        self.worker = worker
        self.lock = lock
        self.config = config or DistributedWorkerConfig()
        self._stopping = False

    def stop(self) -> None:
        self._stopping = True
        self.worker.stop()

    async def process_job(self, job: TaskJob) -> ExecutionRecord:
        token: str | None = None
        lock_name = f"task:{job.task_name}:{job.job_id}"
        try:
            if self.lock is not None and self.config.use_task_lock:
                token = await self.lock.acquire(lock_name, ttl_seconds=self.config.lock_ttl_seconds)
                if token is None:
                    # Another worker holds the lock; re-queue is left to the caller/ops.
                    raise RuntimeError(f"could not acquire lock for {lock_name}")

            record = await self.worker.run(job.task_name, job.metadata)
            await self.queue.ack(job.job_id)
            return record
        finally:
            if self.lock is not None and token is not None:
                await self.lock.release(lock_name, token)

    async def poll_once(self) -> ExecutionRecord | None:
        if self._stopping:
            return None
        job = await self.queue.dequeue(timeout=self.config.poll_timeout)
        if job is None:
            return None
        return await self.process_job(job)

    async def run_forever(self, stop_event: asyncio.Event | None = None) -> None:
        event = stop_event or asyncio.Event()
        while not event.is_set() and not self._stopping:
            try:
                await self.poll_once()
            except Exception:
                # Keep the loop alive; production should log via structured logger.
                await asyncio.sleep(0.1)
