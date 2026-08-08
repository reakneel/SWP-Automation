import pytest

from core.config.settings import Settings
from core.notification.base import NotificationChannel, NotificationService
from core.scheduler.models import Job
from core.scheduler.service import Scheduler


class MemoryChannel(NotificationChannel):
    name = "memory"

    def __init__(self) -> None:
        self.messages: list[str] = []

    async def send(self, message: str, **kwargs: object) -> None:
        self.messages.append(message)


@pytest.mark.asyncio
async def test_notification_service() -> None:
    service = NotificationService()
    channel = MemoryChannel()
    service.register(channel)

    await service.send("memory", "hello")

    assert channel.messages == ["hello"]


def test_scheduler_registry() -> None:
    scheduler = Scheduler()

    async def callback() -> str:
        return "done"

    scheduler.add_job(Job(id="job-1", task_name="example.hello", trigger="manual"), callback)

    assert [job.id for job in scheduler.list_jobs()] == ["job-1"]


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.app_name == "swp-automation"
    assert settings.environment == "development"
