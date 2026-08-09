from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from core.scheduler.models import Job


class Scheduler:
    """Framework-neutral scheduler with an async interval loop.

    The registry remains backend-neutral; a production APScheduler adapter can
    consume the same Job definitions without changing tasks.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._callbacks: dict[str, Callable[[], Awaitable[object]]] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._stopping = False

    def add_job(self, job: Job, callback: Callable[[], Awaitable[object]]) -> None:
        if job.id in self._jobs:
            raise ValueError(f"Job already exists: {job.id}")
        self._jobs[job.id] = job
        self._callbacks[job.id] = callback

    def remove_job(self, job_id: str) -> None:
        task = self._tasks.pop(job_id, None)
        if task:
            task.cancel()
        self._jobs.pop(job_id, None)
        self._callbacks.pop(job_id, None)

    def list_jobs(self) -> list[Job]:
        return list(self._jobs.values())

    async def run_now(self, job_id: str) -> object:
        if job_id not in self._callbacks:
            raise KeyError(job_id)
        return await self._callbacks[job_id]()

    async def start(self) -> None:
        self._stopping = False
        for job in self._jobs.values():
            if job.enabled and job.trigger == "interval" and job.id not in self._tasks:
                self._tasks[job.id] = asyncio.create_task(self._loop(job))

    async def stop(self) -> None:
        self._stopping = True
        tasks = list(self._tasks.values())
        self._tasks.clear()
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _loop(self, job: Job) -> None:
        while not self._stopping:
            await asyncio.sleep(max(1, job.seconds))
            if self._stopping:
                break
            try:
                await self.run_now(job.id)
            except asyncio.CancelledError:
                raise
            except Exception:
                # Execution errors are recorded by the executor; scheduling
                # must remain alive for subsequent runs.
                continue
