from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PluginMetadata:
    name: str
    version: str = "0.1.0"
    description: str = ""
    tags: list[str] = field(default_factory=list)


class Plugin(ABC):
    """Base contract for modular automation plugins."""

    metadata: PluginMetadata

    async def startup(self) -> None:
        return None

    async def shutdown(self) -> None:
        return None

    def tasks(self) -> list[Any]:
        return []
