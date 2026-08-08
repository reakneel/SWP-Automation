from __future__ import annotations

from collections.abc import Awaitable, Callable

from core.scheduler.models import Job


class Scheduler:
    """Framework-neutral scheduler registry.

    A production adapter (APScheduler, cron, or another backend) can consume
    the registered jobs without coupling task implementations to scheduling.
    """

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._callbacks: dict[str, Callable[[], Awaitable[object]]] = {}

    def add_job(self, job: Job, callback: Callable[[], Awaitable[object]]) -> None:
        if job.id in self._jobs:
            raise ValueError(f"Job already exists: {job.id}")
        self._jobs[job.id] = job
        self._callbacks[job.id] = callback

    def remove_job(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)
        self._callbacks.pop(job_id, None)

    def list_jobs(self) -> list[Job]:
        return list(self._jobs.values())

    async def run_now(self, job_id: str) -> object:
        if job_id not in self._callbacks:
            raise KeyError(job_id)
        return await self._callbacks[job_id]()
