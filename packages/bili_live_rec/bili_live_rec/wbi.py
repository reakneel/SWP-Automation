"""Bilibili WBI sign + anonymous buvid3 (nav key mixin)."""
from __future__ import annotations

import hashlib
import time
import urllib.parse
import uuid
from typing import Any

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
WBI_WEB_LOCATION = "444.8"
KEY_MAP = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 34, 44, 52,
]
UPDATE_INTERVAL = 2 * 60 * 60


def fake_buvid3() -> str:
    u = str(uuid.uuid4()).upper().replace("-", "")
    return f"{u[0:8]}-{u[8:12]}-{u[12:16]}-{u[16:20]}-{u[20:]}infoc"


def _extract_key(url: str | None) -> str | None:
    if not url:
        return None
    slash, dot = url.rfind("/"), url.find(".", url.rfind("/"))
    return url[slash + 1 : dot] if slash != -1 and dot != -1 else None


class Wbi:
    def __init__(self, session: Any) -> None:
        self.session = session
        self.key: str | None = None
        self.last_update = 0.0

    def _headers(self) -> dict[str, str]:
        return {"User-Agent": UA, "Referer": "https://www.bilibili.com/"}

    def update_key(self) -> None:
        r = self.session.get(
            "https://api.bilibili.com/x/web-interface/nav",
            headers=self._headers(),
            timeout=10,
        ).json()
        data = r.get("data") or {}
        img = data.get("wbi_img", {}).get("img_url", "")
        sub = data.get("wbi_img", {}).get("sub_url", "")
        img_key, sub_key = _extract_key(img), _extract_key(sub)
        if not (img_key and sub_key):
            raise RuntimeError(f"failed to fetch wbi key: {r}")
        full = img_key + sub_key
        self.key = "".join(full[KEY_MAP[i]] for i in range(32))
        self.last_update = time.time()

    def ensure(self) -> None:
        if not self.key or time.time() - self.last_update >= UPDATE_INTERVAL:
            self.update_key()

    def sign(self, params: dict[str, Any]) -> None:
        if not self.key:
            self.update_key()
        sanitized = {k: "".join(c for c in str(v) if c not in "!'()*") for k, v in params.items()}
        sanitized["wts"] = str(int(time.time()))
        content = urllib.parse.urlencode(dict(sorted(sanitized.items())), quote_via=urllib.parse.quote)
        assert self.key is not None
        params["w_rid"] = hashlib.md5((content + self.key).encode()).hexdigest()
        params["wts"] = sanitized["wts"]
