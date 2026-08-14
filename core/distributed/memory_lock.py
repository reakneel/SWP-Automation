from __future__ import annotations

import uuid


class InMemoryDistributedLock:
    """Process-local lock for tests mirroring RedisDistributedLock semantics."""

    def __init__(self, prefix: str = "automation:lock") -> None:
        self.prefix = prefix
        self._locks: dict[str, str] = {}

    async def acquire(self, name: str, ttl_seconds: int = 30) -> str | None:
        key = f"{self.prefix}:{name}"
        if key in self._locks:
            return None
        token = uuid.uuid4().hex
        self._locks[key] = token
        return token

    async def release(self, name: str, token: str) -> bool:
        key = f"{self.prefix}:{name}"
        if self._locks.get(key) == token:
            del self._locks[key]
            return True
        return False
