from __future__ import annotations


class ApiKeyAuthenticator:
    """Simple shared-secret API key gate. Disabled when no keys are configured."""

    def __init__(self, api_keys: list[str] | None = None) -> None:
        self._keys = {k.strip() for k in (api_keys or []) if k and k.strip()}

    @property
    def enabled(self) -> bool:
        return bool(self._keys)

    def verify(self, api_key: str | None) -> bool:
        if not self.enabled:
            return True
        if not api_key:
            return False
        return api_key.strip() in self._keys
