from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True, frozen=True)
class ResourceConfig:
    enabled: bool = True
    sources: list[str] = field(default_factory=list)
    notify_on_new: bool = True
    notify_on_change: bool = True
