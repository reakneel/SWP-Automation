import pytest

from modules.resource.models import Resource
from modules.resource.services import InMemoryResourceRepository, ResourceSource, ResourceUpdater


class Source(ResourceSource):
    name = "test-source"

    def __init__(self, resources: list[Resource]) -> None:
        self.resources = resources

    async def fetch(self):
        return self.resources


@pytest.mark.asyncio
async def test_resource_upsert_detects_new_and_changed() -> None:
    repository = InMemoryResourceRepository()
    updater = ResourceUpdater(repository)
    first = Resource(id="1", title="A", source="test")

    result = await updater.update(Source([first]))
    assert result[0].is_new is True
    assert result[0].changed is False

    result = await updater.update(Source([Resource(id="1", title="B", source="test")]))
    assert result[0].is_new is False
    assert result[0].changed is True
