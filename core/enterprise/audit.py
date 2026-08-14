from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class AuditEvent:
    action: str
    tenant_id: str
    actor: str
    resource: str
    detail: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "action": self.action,
            "tenant_id": self.tenant_id,
            "actor": self.actor,
            "resource": self.resource,
            "detail": self.detail,
            "created_at": self.created_at,
        }


class AuditLog:
    """In-memory audit trail suitable for single-node and tests."""

    def __init__(self, max_events: int = 5000) -> None:
        self._events: deque[AuditEvent] = deque(maxlen=max_events)
        self._lock = Lock()

    def record(self, event: AuditEvent) -> AuditEvent:
        with self._lock:
            self._events.append(event)
        return event

    def list(
        self,
        *,
        limit: int = 100,
        tenant_id: str | None = None,
    ) -> list[AuditEvent]:
        with self._lock:
            items = list(reversed(self._events))
        if tenant_id:
            items = [e for e in items if e.tenant_id == tenant_id]
        return items[: max(1, min(limit, 1000))]
