from __future__ import annotations

import asyncio
import signal

from core.runtime import runtime
from core.worker.runtime import Worker


async def main() -> None:
    worker = Worker(runtime.executor)
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)
    await stop_event.wait()
    worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
