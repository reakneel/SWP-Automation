"""Highest-quality Bilibili VOD + cover via yt-dlp when available."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


class DownloadError(RuntimeError):
    pass


def ensure_yt_dlp() -> str:
    exe = shutil.which("yt-dlp")
    if not exe:
        raise DownloadError(
            "yt-dlp not found on PATH. Install: pip install yt-dlp "
            "(or system package). Required for highest-quality Bilibili VOD."
        )
    return exe


def parse_bvid(url_or_id: str) -> str:
    text = url_or_id.strip()
    if text.upper().startswith("BV"):
        return text.split("?")[0].split("/")[-1]
    for part in text.replace("?", "/").split("/"):
        if part.upper().startswith("BV"):
            return part
    raise DownloadError(f"cannot parse BVid from: {url_or_id}")


def video_url(bvid: str) -> str:
    return f"https://www.bilibili.com/video/{bvid}"


def fetch_info(bvid: str) -> dict[str, Any]:
    exe = ensure_yt_dlp()
    url = video_url(bvid)
    cmd = [exe, "-J", "--no-download", url]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise DownloadError(f"yt-dlp info failed: {(proc.stderr or '')[-400:]}")
    return json.loads(proc.stdout)


def download_best(bvid: str, out_dir: Path, *, dry_run: bool = False) -> dict[str, Any]:
    """Download best video+audio merge and thumbnail (cover)."""
    exe = ensure_yt_dlp()
    out_dir.mkdir(parents=True, exist_ok=True)
    url = video_url(bvid)
    info = fetch_info(bvid)
    title = str(info.get("title") or bvid)
    if dry_run:
        return {
            "bvid": bvid,
            "title": title,
            "dry_run": True,
            "url": url,
            "formats_hint": "bestvideo+bestaudio/best",
            "thumbnail": info.get("thumbnail"),
        }

    media_tmpl = str(out_dir / "%(id)s.%(ext)s")
    cmd = [
        exe,
        "-f",
        "bestvideo*+bestaudio/best",
        "--merge-output-format",
        "mp4",
        "--write-thumbnail",
        "--convert-thumbnails",
        "jpg",
        "-o",
        media_tmpl,
        "--no-playlist",
        url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if proc.returncode != 0:
        raise DownloadError(f"yt-dlp download failed: {(proc.stderr or '')[-600:]}")

    videos = list(out_dir.glob("*.mp4")) + list(out_dir.glob("*.mkv")) + list(out_dir.glob("*.webm"))
    covers = list(out_dir.glob("*.jpg")) + list(out_dir.glob("*.png")) + list(out_dir.glob("*.webp"))
    video_path = str(videos[0]) if videos else ""
    cover_path = str(covers[0]) if covers else ""
    return {
        "bvid": bvid,
        "title": title,
        "url": url,
        "video_path": video_path,
        "cover_path": cover_path,
        "description": info.get("description") or "",
        "uploader": info.get("uploader") or "",
        "duration": info.get("duration"),
        "dry_run": False,
    }
