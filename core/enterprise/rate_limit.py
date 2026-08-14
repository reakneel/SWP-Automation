from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock


@dataclass(slots=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    limit: int
    reset_after_seconds: float


class RateLimiter:
    """Fixed-window rate limiter keyed by tenant (or other scope string)."""

    def __init__(self, *, limit: int = 60, window_seconds: float = 60.0) -> None:
        self.limit = max(1, limit)
        self.window_seconds = max(1.0, window_seconds)
        self._windows: dict[str, tuple[float, int]] = {}
        self._lock = Lock()

    def check(self, key: str) -> RateLimitResult:
        now = time.monotonic()
        with self._lock:
            window_start, count = self._windows.get(key, (now, 0))
            if now - window_start >= self.window_seconds:
                window_start, count = now, 0
            if count >= self.limit:
                self._windows[key] = (window_start, count)
                reset = self.window_seconds - (now - window_start)
                return RateLimitResult(False, 0, self.limit, max(0.0, reset))
            count += 1
            self._windows[key] = (window_start, count)
            remaining = max(0, self.limit - count)
            reset = self.window_seconds - (now - window_start)
            return RateLimitResult(True, remaining, self.limit, max(0.0, reset))
