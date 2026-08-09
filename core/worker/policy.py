from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    multiplier: float = 2.0

    def delay(self, attempt: int) -> float:
        return min(self.max_delay, self.initial_delay * (self.multiplier ** max(0, attempt - 1)))
