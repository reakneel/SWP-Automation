from __future__ import annotations

from pathlib import Path


def work_dir(meta: dict) -> Path:
    return Path(str(meta.get("work_dir") or "data/bili_to_youtube"))


def job_dir(meta: dict, bvid: str) -> Path:
    return work_dir(meta) / bvid


def brief_path(meta: dict, bvid: str) -> Path:
    return job_dir(meta, bvid) / "brief.md"


def confirm_path(meta: dict, bvid: str) -> Path:
    return job_dir(meta, bvid) / "CONFIRMED"


def manifest_path(meta: dict, bvid: str) -> Path:
    return job_dir(meta, bvid) / "manifest.json"
