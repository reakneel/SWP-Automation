from __future__ import annotations

import asyncio
from dataclasses import dataclass

from core.task.execution import ExecutionRecord, ExecutionStatus
from core.task.registry import TaskRegistry
from core.worker.executor import TaskExecutor
from core.worker.policy import RetryPolicy


@dataclass(slots=True)
class WorkerConfig:
    concurrency: int = 4
    timeout_seconds: float = 300.0
    retry: RetryPolicy = RetryPolicy()


class Worker:
    def __init__(self, executor: TaskExecutor, config: WorkerConfig | None = None) -> None:
        self.executor = executor
        self.config = config or WorkerConfig()
        self._semaphore = asyncio.Semaphore(self.config.concurrency)
        self._stopping = False

    async def run(self, task_name: str, metadata: dict | None = None) -> ExecutionRecord:
        if self._stopping:
            raise RuntimeError("worker is stopping")
        async with self._semaphore:
            last: ExecutionRecord | None = None
            for attempt in range(1, self.config.retry.max_attempts + 1):
                try:
                    last = await asyncio.wait_for(
                        self.executor.execute(task_name, metadata),
                        timeout=self.config.timeout_seconds,
                    )
                    if last.status == ExecutionStatus.SUCCESS or attempt >= self.config.retry.max_attempts:
                        return last
                except asyncio.TimeoutError:
                    if attempt >= self.config.retry.max_attempts:
                        raise
                await asyncio.sleep(self.config.retry.delay(attempt))
            assert last is not None
            return last

    def stop(self) -> None:
        self._stopping = True
