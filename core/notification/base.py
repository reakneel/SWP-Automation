from __future__ import annotations

from abc import ABC, abstractmethod


class NotificationChannel(ABC):
    name: str

    @abstractmethod
    async def send(self, message: str, **kwargs: object) -> None:
        raise NotImplementedError


class NotificationService:
    def __init__(self) -> None:
        self._channels: dict[str, NotificationChannel] = {}

    def register(self, channel: NotificationChannel) -> None:
        if channel.name in self._channels:
            raise ValueError(f"Notification channel already exists: {channel.name}")
        self._channels[channel.name] = channel

    async def send(self, channel: str, message: str, **kwargs: object) -> None:
        target = self._channels.get(channel)
        if target is None:
            raise KeyError(channel)
        await target.send(message, **kwargs)

    def list_channels(self) -> list[str]:
        return sorted(self._channels)
