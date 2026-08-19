"""YouTube upload gate — real upload only after confirm; dry-run by default."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class UploadError(RuntimeError):
    pass


def upload_video(
    *,
    video_path: str,
    cover_path: str,
    title: str,
    description: str,
    tags: list[str],
    dry_run: bool = True,
    client_secrets: str | None = None,
) -> dict[str, Any]:
    """Upload to YouTube. dry_run default; private privacy when real."""
    if not video_path or not Path(video_path).is_file():
        raise UploadError(f"video not found: {video_path}")

    plan = {
        "video_path": video_path,
        "cover_path": cover_path,
        "title": title,
        "description": description[:5000],
        "tags": tags,
        "privacy_status": "private",
    }
    if dry_run:
        return {"uploaded": False, "dry_run": True, "plan": plan}

    secrets = client_secrets or ""
    if not secrets or not Path(secrets).is_file():
        raise UploadError(
            "youtube client_secrets JSON required for real upload "
            "(Google Cloud OAuth client). Pass metadata.youtube_client_secrets"
        )

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:
        raise UploadError(
            "Install YouTube deps: pip install google-api-python-client "
            "google-auth-oauthlib google-auth-httplib2"
        ) from exc

    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    token_path = Path(secrets).with_name("youtube_token.json")
    creds = None
    if token_path.is_file():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secrets, scopes)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    youtube = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:30],
            "categoryId": "22",
        },
        "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        _status, response = request.next_chunk()
    video_id = response.get("id")
    result: dict[str, Any] = {
        "uploaded": True,
        "dry_run": False,
        "video_id": video_id,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "privacy": "private",
    }
    if cover_path and Path(cover_path).is_file() and video_id:
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(cover_path),
            ).execute()
            result["thumbnail_set"] = True
        except Exception:
            result["thumbnail_set"] = False
    return result


def save_manifest(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
