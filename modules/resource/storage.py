from __future__ import annotations

import json
from pathlib import Path

from modules.resource.models import Resource
from modules.resource.services import ResourceRepository


class JsonResourceRepository(ResourceRepository):
    """Small durable repository for M2; replaceable by SQL in a later milestone."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._items: dict[str, Resource] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self._items = {item["id"]: Resource(**item) for item in payload}
        self._loaded = True

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [
            {"id": r.id, "title": r.title, "source": r.source, "url": r.url, "version": r.version,
             "published_at": r.published_at.isoformat() if r.published_at else None, "metadata": r.metadata}
            for r in self._items.values()
        ]
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    async def get(self, resource_id: str) -> Resource | None:
        self._ensure_loaded()
        return self._items.get(resource_id)

    async def upsert(self, resource: Resource):
        self._ensure_loaded()
        previous = self._items.get(resource.id)
        self._items[resource.id] = resource
        self._save()
        from modules.resource.models import ResourceUpdate
        return ResourceUpdate(resource, previous is None, previous is not None and previous != resource)

    async def list(self) -> list[Resource]:
        self._ensure_loaded()
        return list(self._items.values())
