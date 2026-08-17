"""Stoppable ffmpeg / bounded record helpers (asyncio — no blocking subprocess.run)."""
from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from typing import Any
import re

from packages.bili_live_rec.bili_live_rec.wbi import UA


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|\s]+', "_", str(name))[:80] or "untitled"


def build_ffmpeg_cmd(url: str, out: Path, *, fmt: str = "flv") -> list[str]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "warning",
        "-nostdin",
        "-user_agent",
        UA,
        "-headers",
        "Referer: https://live.bilibili.com/\r\n",
        "-i",
        url,
        "-c",
        "copy",
    ]
    if fmt == "flv":
        cmd += ["-f", "flv", "-flvflags", "no_duration_filesize"]
    elif fmt == "mp4":
        cmd += ["-movflags", "frag_keyframes+empty_moov"]
    cmd.append(str(out))
    return cmd


async def record_once(
    url: str,
    out: Path,
    *,
    fmt: str = "flv",
    max_seconds: float = 60.0,
) -> dict[str, Any]:
    """Run one ffmpeg session with a hard time bound (async, stoppable)."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found on PATH")

    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = build_ffmpeg_cmd(url, out, fmt=fmt)
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    )
    timed_out = False
    stderr = b""
    try:
        try:
            _stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=max_seconds)
        except TimeoutError:
            timed_out = True
            proc.terminate()
            try:
                _stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            except TimeoutError:
                proc.kill()
                _stdout, stderr = await proc.communicate()
    except asyncio.CancelledError:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.communicate(), timeout=5)
        except TimeoutError:
            proc.kill()
            await proc.communicate()
        raise

    size = out.stat().st_size if out.exists() else 0
    return {
        "path": str(out),
        "bytes": size,
        "returncode": proc.returncode,
        "timed_out": timed_out,
        "stderr_tail": (stderr or b"").decode(errors="replace")[-500:],
        "ok": size > 0,
    }
