import asyncio

import pytest

from core.scheduler.models import Job
from core.scheduler.service import Scheduler
from core.worker.policy import RetryPolicy


@pytest.mark.asyncio
async def test_scheduler_start_stop_and_run_now() -> None:
    scheduler = Scheduler()
    called = 0

    async def callback():
        nonlocal called
        called += 1

    scheduler.add_job(Job(id="j1", task_name="x", seconds=1), callback)
    await scheduler.start()
    await scheduler.run_now("j1")
    await scheduler.stop()
    assert called == 1


def test_retry_policy_caps_delay() -> None:
    policy = RetryPolicy(max_attempts=4, initial_delay=2, max_delay=5)
    assert policy.delay(1) == 2
    assert policy.delay(2) == 4
    assert policy.delay(3) == 5
