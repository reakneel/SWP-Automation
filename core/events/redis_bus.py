from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any


class RedisEventBus:
    """Redis Streams event transport; keeps EventBus consumers provider-agnostic."""

    def __init__(self, redis: Any, stream_prefix: str = "automation:events") -> None:
        self.redis = redis
        self.stream_prefix = stream_prefix

    def _stream(self, event_type: str) -> str:
        return f"{self.stream_prefix}:{event_type}"

    async def publish(self, event_type: str, payload: dict[str, Any]) -> str:
        return await self.redis.xadd(
            self._stream(event_type),
            {"payload": json.dumps(payload, default=str)},
        )

    async def consume(
        self,
        event_type: str,
        handler: Callable[[dict[str, Any]], Awaitable[None]],
        count: int = 10,
        block_ms: int = 1000,
    ) -> None:
        streams = {self._stream(event_type): "$"}
        while True:
            batches = await self.redis.xread(streams, count=count, block=block_ms)
            for _, entries in batches or []:
                for _, values in entries:
                    payload = values.get(b"payload", values.get("payload"))
                    await handler(json.loads(payload))
