# M5.7 Distributed Runtime

Shared task queue and multi-worker execution on top of M3 Redis primitives.

## Components

| Piece | Role |
|-------|------|
| `TaskJob` | Serializable work unit (`job_id`, `task_name`, `metadata`) |
| `InMemoryTaskQueue` | Single-process queue for tests / dev |
| `RedisTaskQueue` | Redis list queue (`RPUSH` / `BLPOP`) + processing hash |
| `DistributedWorker` | Dequeue → optional distributed lock → `Worker.run` → ack |
| `InMemoryDistributedLock` | Test double for `RedisDistributedLock` |

## Flow

```text
API / Scheduler
      |
      v
 TaskQueue.enqueue(TaskJob)
      |
      +---- worker-1 DistributedWorker.poll_once
      +---- worker-2 DistributedWorker.poll_once
      |
      v
 TaskExecutor (timeout, retries via Worker)
```

## Settings (`SWP_` prefix)

| Variable | Default | Notes |
|----------|---------|-------|
| `REDIS_URL` | unset | When set, worker uses Redis queue + lock |
| `TASK_QUEUE_KEY` | `automation:tasks` | Redis list key |
| `WORKER_ID` | `worker-1` | Identity for logging/ops |
| `WORKER_POLL_TIMEOUT` | `1.0` | Dequeue block seconds |

## Local usage

```python
from core.distributed import DistributedWorker, InMemoryTaskQueue, TaskJob
from core.distributed.memory_lock import InMemoryDistributedLock
from core.worker.runtime import Worker
from core.runtime import AutomationRuntime

runtime = AutomationRuntime.create()
queue = InMemoryTaskQueue()
worker = DistributedWorker(queue, Worker(runtime.executor), lock=InMemoryDistributedLock())

await queue.enqueue(TaskJob(task_name="daily.report"))
record = await worker.poll_once()
```

## Out of scope

- Exactly-once semantics across crashes (processing hash is best-effort)
- Horizontal scheduler leader election
- Cross-region replication
