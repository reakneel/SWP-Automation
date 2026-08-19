from __future__ import annotations

from pathlib import Path

import pytest

import packages.bili_to_youtube.bili_to_youtube.plugin as plugin_mod
from core.runtime import AutomationRuntime
from packages.bili_to_youtube.bili_to_youtube.brief import parse_brief_sections, render_template
from packages.bili_to_youtube.bili_to_youtube.download import parse_bvid
from packages.bili_to_youtube.bili_to_youtube.plugin import BiliToYoutubePlugin


def test_parse_bvid() -> None:
    assert parse_bvid("BV1xx411c7mD").startswith("BV")
    assert "BV" in parse_bvid("https://www.bilibili.com/video/BV1xx411c7mD?spm=1")


def test_brief_template_and_parse() -> None:
    text = render_template(
        title="T",
        description="D",
        tags="a,b",
        source_url="https://x",
        bvid="BV1",
    )
    sections = parse_brief_sections(text)
    assert sections["title"] == "T"
    assert "D" in sections["description"]


@pytest.mark.asyncio
async def test_pipeline_awaits_confirmation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_download(bvid: str, out_dir: Path, *, dry_run: bool = False):
        out_dir.mkdir(parents=True, exist_ok=True)
        video = out_dir / "vid.mp4"
        cover = out_dir / "cover.jpg"
        if not dry_run:
            video.write_bytes(b"fake")
            cover.write_bytes(b"fake")
        return {
            "bvid": bvid,
            "title": "Demo",
            "url": f"https://www.bilibili.com/video/{bvid}",
            "video_path": str(video),
            "cover_path": str(cover),
            "description": "orig",
            "dry_run": dry_run,
        }

    monkeypatch.setattr(plugin_mod, "download_best", fake_download)
    monkeypatch.setattr(plugin_mod, "parse_bvid", lambda x: "BV1test00000")

    rt = AutomationRuntime.create()
    await rt.plugins.load(BiliToYoutubePlugin())
    meta = {"bvid": "BV1test00000", "work_dir": str(tmp_path), "dry_run": False}
    rec = await rt.executor.execute("bili_yt.run", meta)
    assert rec.status.value == "success", rec.message
    assert rec.message == "awaiting_confirmation"
    assert (tmp_path / "BV1test00000" / "brief.md").is_file()

    conf = await rt.executor.execute("bili_yt.confirm", meta)
    assert conf.status.value == "success"
    up = await rt.executor.execute("bili_yt.upload", {**meta, "dry_run": True})
    assert up.status.value == "success"
    assert up.data.get("dry_run") is True
