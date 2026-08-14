from __future__ import annotations

import asyncio
import signal

from core.config.settings import get_settings
from core.distributed.queue import RedisTaskQueue
from core.distributed.worker import DistributedWorker, DistributedWorkerConfig
from core.runtime import runtime
from core.worker.runtime import Worker


async def main() -> None:
    settings = get_settings()
    local_worker = Worker(runtime.executor)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    if settings.redis_url:
        try:
            from redis.asyncio import Redis

            from core.events.lock import RedisDistributedLock

            redis = Redis.from_url(settings.redis_url, decode_responses=True)
            queue = RedisTaskQueue(redis, key=settings.task_queue_key)
            lock = RedisDistributedLock(redis)
            distributed = DistributedWorker(
                queue,
                local_worker,
                lock=lock,
                config=DistributedWorkerConfig(
                    worker_id=settings.worker_id,
                    poll_timeout=settings.worker_poll_timeout,
                ),
            )
            await distributed.run_forever(stop_event)
            await redis.aclose()
            return
        except Exception:
            # Fall through to idle local worker if redis is unavailable at startup.
            pass

    # No Redis: keep process alive for health/orchestration; jobs are run via API executor.
    await stop_event.wait()
    local_worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
