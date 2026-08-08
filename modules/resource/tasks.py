from __future__ import annotations

from core.task.base import Task, TaskContext, TaskResult
from modules.resource.services import ResourceSource, ResourceUpdater


class ResourceUpdateTask(Task):
    name = "resource.update"
    description = "Fetch resources from a configured source and upsert changes."

    def __init__(self, updater: ResourceUpdater, source: ResourceSource) -> None:
        self.updater = updater
        self.source = source

    async def run(self, context: TaskContext) -> TaskResult:
        updates = await self.updater.update(self.source)
        created = sum(item.is_new for item in updates)
        changed = sum(item.changed for item in updates)
        return TaskResult.ok(
            "resource update completed",
            source=self.source.name,
            total=len(updates),
            created=created,
            changed=changed,
        )


class ResourceSyncTask(ResourceUpdateTask):
    name = "resource.sync"
    description = "Synchronize resources from the configured source."
