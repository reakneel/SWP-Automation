"""Room info + stream URL resolution (no ffmpeg)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from packages.bili_live_rec.bili_live_rec.wbi import UA, WBI_WEB_LOCATION, Wbi, fake_buvid3

LIVE_API = "https://api.live.bilibili.com"
QN_NAME = {
    30000: "杜比视界",
    25000: "杜比全景声",
    20000: "4K超清",
    15000: "蓝光杜比",
    10000: "原画",
    401: "蓝光(网页)",
    400: "蓝光",
    250: "超清",
    150: "高清",
    80: "流畅",
}


def parse_room_input(raw: str) -> str:
    m = re.search(r"bilibili\.com/(\d+)", raw)
    if m:
        return m.group(1)
    if re.fullmatch(r"\d+", raw.strip()):
        return raw.strip()
    raise ValueError(f"cannot parse room id: {raw}")


@dataclass
class RoomState:
    room_id: int
    short_id: int
    anchor_uid: int
    title: str
    live_status: int
    live_start_time: int = 0


class BiliRoomClient:
    def __init__(self, session: Any, *, cookie: str = "") -> None:
        self.session = session
        self.cookie = cookie
        self.wbi = Wbi(session)
        if not any(c.name == "buvid3" for c in session.cookies):
            session.cookies.set("buvid3", fake_buvid3(), domain=".bilibili.com")

    def headers(self, room_ref: str = "") -> dict[str, str]:
        h = {
            "User-Agent": UA,
            "Referer": f"https://live.bilibili.com/{room_ref or ''}",
        }
        if self.cookie:
            h["Cookie"] = self.cookie
        return h

    def _get(self, url: str, params: dict | None = None) -> dict:
        r = self.session.get(url, params=params, headers=self.headers(), timeout=15)
        r.raise_for_status()
        return r.json()

    def get_room_info(self, raw: str) -> RoomState:
        rid = parse_room_input(raw)
        try:
            d = self._get(f"{LIVE_API}/room/v1/Room/get_info", {"room_id": rid})["data"]
            return RoomState(
                room_id=int(d["room_id"]),
                short_id=int(d.get("short_id") or 0),
                anchor_uid=int(d["uid"]),
                title=str(d.get("title") or ""),
                live_status=int(d.get("live_status") or 0),
                live_start_time=int(d.get("live_start_time") or 0),
            )
        except Exception:
            self.wbi.ensure()
            params: dict[str, Any] = {"room_id": rid, "web_location": WBI_WEB_LOCATION}
            self.wbi.sign(params)
            d = self._get(f"{LIVE_API}/xlive/web-room/v1/index/getInfoByRoom", params)["data"]
            ri = d["room_info"]
            return RoomState(
                room_id=int(ri["room_id"]),
                short_id=0,
                anchor_uid=int(ri["uid"]),
                title=str(ri.get("title") or ""),
                live_status=int(ri.get("live_status") or 0),
                live_start_time=int(ri.get("live_start_time") or 0),
            )

    def get_master_streams(self, room: RoomState, qn: int) -> dict[int, list[dict]]:
        params = {
            "cid": room.room_id,
            "mid": room.anchor_uid,
            "pt": "web",
            "p2p_type": -1,
            "net": 0,
            "free_type": 0,
            "build": 0,
            "feature": 2,
            "qn": qn,
            "drm_type": 0,
            "codec": "0,1",
        }
        r = self.session.get(
            f"{LIVE_API}/xlive/play-gateway/master/url",
            params=params,
            headers=self.headers(str(room.room_id)),
            timeout=15,
        )
        if r.status_code == 200 and r.text.startswith("#EXTM3U"):
            return parse_master_m3u8(r.text)
        return {}

    def get_play_info_streams(self, room: RoomState, qn: int) -> dict[int, list[dict]]:
        self.wbi.ensure()
        params: dict[str, Any] = {
            "room_id": str(room.room_id),
            "qn": str(qn),
            "platform": "html5",
            "protocol": "0,1",
            "format": "0,1,2",
            "codec": "0",
            "dolby": "5",
            "web_location": WBI_WEB_LOCATION,
        }
        self.wbi.sign(params)
        data = self._get(f"{LIVE_API}/xlive/web-room/v2/index/getRoomPlayInfo", params)["data"]
        if not data.get("playurl_info", {}).get("playurl"):
            return {}
        result: dict[int, list[dict]] = {}
        for stream in data["playurl_info"]["playurl"]["stream"]:
            for fmt in stream.get("format", []):
                for codec in fmt.get("codec", []):
                    cur = int(codec["current_qn"])
                    for ui in codec.get("url_info", []):
                        url = f"{ui['host']}{codec['base_url']}{ui['extra']}"
                        result.setdefault(cur, []).append(
                            {
                                "url": url,
                                "avc": codec.get("codec_name") == "avc",
                                "cdn": ui.get("extra", ""),
                                "format": fmt.get("format_name"),
                            }
                        )
        return result

    def resolve_stream(self, room: RoomState, qn: int = 10000) -> dict[str, Any]:
        streams: dict[int, list[dict]] = {}
        try:
            streams = self.get_master_streams(room, qn)
        except Exception:
            streams = {}
        if streams:
            avail = [q for q in streams if q <= qn] or list(streams)
            pick = max(avail)
            best = streams[pick][0]
            return {
                "url": best["url"],
                "qn": pick,
                "qn_name": QN_NAME.get(pick, str(pick)),
                "proto": "hls",
                "avc": best.get("avc"),
                "cdn": best.get("cdn"),
                "channel": "play-gateway",
            }
        streams = self.get_play_info_streams(room, qn)
        if not streams:
            raise RuntimeError("no stream (offline, paid room, or region lock)")
        avail = [q for q in streams if q <= qn] or list(streams)
        pick = max(avail)
        best = streams[pick][0]
        return {
            "url": best["url"],
            "qn": pick,
            "qn_name": QN_NAME.get(pick, str(pick)),
            "proto": "flv" if best.get("format") == "flv" else "hls",
            "format": best.get("format"),
            "channel": "getRoomPlayInfo",
        }


def parse_master_m3u8(content: str) -> dict[int, list[dict]]:
    lines = content.strip().splitlines()
    result: dict[int, list[dict]] = {}
    cur_qn: int | None = None
    cur_avc = False
    for line in lines:
        if line.startswith("#EXT-X-STREAM-INF"):
            qm = re.search(r"BILI-QN=(\d+)", line)
            cm = re.search(r'CODECS="([^"]+)"', line)
            cur_qn = int(qm.group(1)) if qm else None
            cur_avc = bool(cm and "avc" in cm.group(1).lower())
        elif line.startswith("http") and cur_qn is not None:
            cdn = re.search(r"cdn=([^&]+)", line)
            result.setdefault(cur_qn, []).append(
                {
                    "url": line,
                    "avc": cur_avc,
                    "cdn": cdn.group(1) if cdn else "default",
                }
            )
            cur_qn = None
    for qn in result:
        result[qn].sort(key=lambda x: not x["avc"])
    return dict(sorted(result.items(), key=lambda x: -x[0]))
