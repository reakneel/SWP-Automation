from __future__ import annotations

from core.plugin.base import Plugin, PluginMetadata
from core.task.base import Task
from modules.resource.services import InMemoryResourceRepository, ResourceSource, ResourceUpdater
from modules.resource.tasks import ResourceSyncTask, ResourceUpdateTask


class ResourcePlugin(Plugin):
    metadata = PluginMetadata(
        name="resource",
        version="0.1.0",
        description="Resource discovery, synchronization, and update tasks.",
        tags=["resource", "sync", "update"],
    )

    def __init__(self, source: ResourceSource) -> None:
        repository = InMemoryResourceRepository()
        updater = ResourceUpdater(repository)
        self._tasks = [ResourceUpdateTask(updater, source), ResourceSyncTask(updater, source)]

    def tasks(self) -> list[Task]:
        return self._tasks
