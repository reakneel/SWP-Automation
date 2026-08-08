from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from modules.resource.services import ResourceRepository

router = APIRouter(prefix="/api/v1/resources", tags=["resources"])


class ResourceAPI:
    def __init__(self, repository: ResourceRepository) -> None:
        self.repository = repository

    def router(self) -> APIRouter:
        router = APIRouter(prefix="/api/v1/resources", tags=["resources"])

        @router.get("")
        async def list_resources() -> list[dict]:
            return [asdict(resource) for resource in await self.repository.list()]

        return router
