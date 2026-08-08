from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(slots=True)
class Reminder:
    id: str
    title: str
    due_at: datetime
    message: str = ""
    cancelled: bool = False


class ReminderService:
    def __init__(self) -> None:
        self._items: dict[str, Reminder] = {}

    def create(self, title: str, due_at: datetime, message: str = "") -> Reminder:
        reminder = Reminder(str(uuid4()), title, due_at, message)
        self._items[reminder.id] = reminder
        return reminder

    def cancel(self, reminder_id: str) -> bool:
        reminder = self._items.get(reminder_id)
        if reminder is None:
            return False
        reminder.cancelled = True
        return True

    def list(self) -> list[Reminder]:
        return list(self._items.values())

    def due(self, now: datetime | None = None) -> list[Reminder]:
        now = now or datetime.now(timezone.utc)
        return [r for r in self._items.values() if not r.cancelled and r.due_at <= now]
