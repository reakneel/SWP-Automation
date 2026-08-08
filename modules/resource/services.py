from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from modules.resource.models import Resource, ResourceUpdate


class ResourceSource(ABC):
    """Adapter contract for any external resource provider."""

    name: str

    @abstractmethod
    async def fetch(self) -> Iterable[Resource]:
        raise NotImplementedError


class ResourceRepository(ABC):
    """Persistence boundary for normalized resources."""

    @abstractmethod
    async def get(self, resource_id: str) -> Resource | None:
        raise NotImplementedError

    @abstractmethod
    async def upsert(self, resource: Resource) -> ResourceUpdate:
        raise NotImplementedError

    @abstractmethod
    async def list(self) -> list[Resource]:
        raise NotImplementedError


class InMemoryResourceRepository(ResourceRepository):
    def __init__(self) -> None:
        self._items: dict[str, Resource] = {}

    async def get(self, resource_id: str) -> Resource | None:
        return self._items.get(resource_id)

    async def upsert(self, resource: Resource) -> ResourceUpdate:
        previous = self._items.get(resource.id)
        is_new = previous is None
        changed = previous is not None and previous != resource
        self._items[resource.id] = resource
        return ResourceUpdate(resource=resource, is_new=is_new, changed=changed)

    async def list(self) -> list[Resource]:
        return list(self._items.values())


class ResourceUpdater:
    def __init__(self, repository: ResourceRepository) -> None:
        self.repository = repository

    async def update(self, source: ResourceSource) -> list[ResourceUpdate]:
        updates: list[ResourceUpdate] = []
        for resource in await source.fetch():
            updates.append(await self.repository.upsert(resource))
        return updates
