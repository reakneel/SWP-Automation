from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from core.plugin.base import Plugin, PluginMetadata
from core.task.base import Task, TaskContext, TaskResult
from modules.reminder.service import ReminderService


class ReminderPlugin(Plugin):
    metadata = PluginMetadata(name="reminder", version="0.1.0", description="Create, cancel, list, and trigger reminders.", tags=["reminder"])

    def __init__(self, service: ReminderService | None = None) -> None:
        self.service = service or ReminderService()

    def tasks(self) -> list[Task]:
        return [_CreateTask(self.service), _CancelTask(self.service), _ListTask(self.service), _TriggerTask(self.service)]


class _CreateTask(Task):
    name = "reminder.create"
    description = "Create a reminder from task metadata."
    def __init__(self, service: ReminderService): self.service = service
    async def run(self, context: TaskContext) -> TaskResult:
        due_at = datetime.fromisoformat(str(context.metadata["due_at"]))
        reminder = self.service.create(str(context.metadata["title"]), due_at, str(context.metadata.get("message", "")))
        return TaskResult.ok("reminder created", id=reminder.id)


class _CancelTask(Task):
    name = "reminder.cancel"
    description = "Cancel a reminder."
    def __init__(self, service: ReminderService): self.service = service
    async def run(self, context: TaskContext) -> TaskResult:
        return TaskResult.ok("reminder cancelled", cancelled=self.service.cancel(str(context.metadata["id"])))


class _ListTask(Task):
    name = "reminder.list"
    description = "List reminders."
    def __init__(self, service: ReminderService): self.service = service
    async def run(self, context: TaskContext) -> TaskResult:
        return TaskResult.ok("reminders listed", reminders=[asdict(r) for r in self.service.list()])


class _TriggerTask(Task):
    name = "reminder.trigger"
    description = "Find due reminders."
    def __init__(self, service: ReminderService): self.service = service
    async def run(self, context: TaskContext) -> TaskResult:
        return TaskResult.ok("reminders triggered", reminders=[asdict(r) for r in self.service.due()])
