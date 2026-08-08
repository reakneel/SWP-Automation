from __future__ import annotations

from fastapi import APIRouter

from modules.resource.services import ResourceRepository

router = APIRouter(prefix="/api/v1/resources", tags=["resources"])


@router.get("")
async def list_resources(repository: ResourceRepository) -> list[dict]:
    return [resource.__dict__ for resource in await repository.list()]
