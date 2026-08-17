from __future__ import annotations

from core.config.settings import Settings, get_settings
from integrations.ai.gate import AiSettingsView


def test_ai_disabled_without_key() -> None:
    get_settings.cache_clear()
    s = Settings(ai_api_key=None)
    assert not (s.ai_api_key or "").strip()


def test_ai_settings_view_with_key() -> None:
    view = AiSettingsView(
        enabled=True,
        base_url="https://api.x.ai/v1",
        model="grok-3",
        has_api_key=True,
    )
    assert view.enabled is True


def test_skill_files_exist() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    assert (root / "skills/bili-live/SKILL.md").is_file()
    assert (root / "skills/bili-live/references/tool-schema.json").is_file()
    assert (root / "skills/bili-live/scripts/run_tool.py").is_file()
