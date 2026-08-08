from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True, frozen=True)
class Resource:
    """Normalized resource discovered from an external source."""

    id: str
    title: str
    source: str
    url: str | None = None
    version: str | None = None
    published_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ResourceUpdate:
    resource: Resource
    is_new: bool
    changed: bool = False
