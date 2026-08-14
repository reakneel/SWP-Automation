from __future__ import annotations

import pytest

from core.distributed.memory_lock import InMemoryDistributedLock
from core.distributed.queue import InMemoryTaskQueue, TaskJob
from core.distributed.worker import DistributedWorker
from core.runtime import AutomationRuntime
from core.task.base import Task, TaskContext, TaskResult
from core.task.execution import ExecutionStatus
from core.worker.runtime import Worker


class HelloTask(Task):
    name = "dist.hello"
    description = "distributed hello"

    async def run(self, context: TaskContext) -> TaskResult:
        return TaskResult.ok("hello", echo=context.metadata.get("n", 0))


@pytest.mark.asyncio
async def test_inmemory_queue_enqueue_dequeue() -> None:
    queue = InMemoryTaskQueue()
    job_id = await queue.enqueue(TaskJob(task_name="dist.hello", metadata={"n": 1}))
    assert await queue.size() == 1
    job = await queue.dequeue(timeout=0.2)
    assert job is not None
    assert job.job_id == job_id
    assert job.task_name == "dist.hello"
    await queue.ack(job.job_id)


@pytest.mark.asyncio
async def test_distributed_worker_processes_job() -> None:
    runtime = AutomationRuntime.create()
    runtime.registry.register(HelloTask())
    queue = InMemoryTaskQueue()
    lock = InMemoryDistributedLock()
    distributed = DistributedWorker(queue, Worker(runtime.executor), lock=lock)

    await queue.enqueue(TaskJob(task_name="dist.hello", metadata={"n": 7}))
    record = await distributed.poll_once()
    assert record is not None
    assert record.status is ExecutionStatus.SUCCESS
    assert record.data is not None
    assert record.data.get("echo") == 7


@pytest.mark.asyncio
async def test_lock_prevents_double_acquire() -> None:
    lock = InMemoryDistributedLock()
    t1 = await lock.acquire("task:x")
    t2 = await lock.acquire("task:x")
    assert t1 is not None
    assert t2 is None
    assert await lock.release("task:x", t1) is True
    t3 = await lock.acquire("task:x")
    assert t3 is not None


@pytest.mark.asyncio
async def test_poll_once_returns_none_when_empty() -> None:
    runtime = AutomationRuntime.create()
    distributed = DistributedWorker(InMemoryTaskQueue(), Worker(runtime.executor))
    assert await distributed.poll_once() is None
