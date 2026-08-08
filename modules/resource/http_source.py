from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from modules.resource.models import Resource
from modules.resource.services import ResourceSource


class HttpJsonResourceSource(ResourceSource):
    """Minimal provider adapter for JSON APIs.

    The callable parser keeps HTTP/client policy outside the resource domain.
    """

    def __init__(self, name: str, fetch_json, parser) -> None:
        self.name = name
        self._fetch_json = fetch_json
        self._parser = parser

    async def fetch(self) -> Iterable[Resource]:
        payload: Any = await self._fetch_json()
        return self._parser(payload)
