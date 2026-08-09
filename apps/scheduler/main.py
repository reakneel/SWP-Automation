from __future__ import annotations

import asyncio
import signal

from core.scheduler.service import Scheduler


async def main() -> None:
    scheduler = Scheduler()
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)
    await scheduler.start()
    await stop_event.wait()
    await scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
