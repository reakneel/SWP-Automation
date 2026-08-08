from __future__ import annotations

from collections.abc import Iterable

from modules.resource.models import Resource
from modules.resource.services import ResourceSource


class StaticResourceSource(ResourceSource):
    """Deterministic source useful for local development and tests."""

    name = "static"

    def __init__(self, resources: Iterable[Resource] = ()) -> None:
        self._resources = list(resources)

    async def fetch(self) -> list[Resource]:
        return list(self._resources)
