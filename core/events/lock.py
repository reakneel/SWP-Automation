from __future__ import annotations

import uuid
from typing import Any


class RedisDistributedLock:
    def __init__(self, redis: Any, prefix: str = "automation:lock") -> None:
        self.redis = redis
        self.prefix = prefix

    async def acquire(self, name: str, ttl_seconds: int = 30) -> str | None:
        token = uuid.uuid4().hex
        acquired = await self.redis.set(
            f"{self.prefix}:{name}", token, nx=True, ex=ttl_seconds
        )
        return token if acquired else None

    async def release(self, name: str, token: str) -> bool:
        key = f"{self.prefix}:{name}"
        current = await self.redis.get(key)
        if current is not None and current.decode() == token:
            return bool(await self.redis.delete(key))
        return False
