from __future__ import annotations


class PluginError(Exception):
    """Base plugin runtime error."""


class PluginLoadError(PluginError):
    """Raised when plugin loading fails."""


class PluginConfigError(PluginError):
    """Raised when plugin configuration is invalid."""
