from __future__ import annotations

from core.plugin.base import Plugin, PluginMetadata
from core.task.base import Task, TaskContext, TaskResult
from packages.bili_to_youtube.bili_to_youtube.brief import (
    build_brief_payload,
    parse_brief_sections,
    read_brief,
    write_brief,
)
from packages.bili_to_youtube.bili_to_youtube.download import download_best, parse_bvid
from packages.bili_to_youtube.bili_to_youtube.paths import brief_path, confirm_path, job_dir, manifest_path
from packages.bili_to_youtube.bili_to_youtube.youtube_upload import load_manifest, save_manifest, upload_video


def _bvid(meta: dict) -> str:
    raw = str(meta.get("bvid") or meta.get("url") or meta.get("video") or "")
    if not raw:
        raise ValueError("metadata.bvid or url is required")
    return parse_bvid(raw)


class _DownloadTask(Task):
    name = "bili_yt.download"
    description = "Download Bilibili VOD at highest quality + cover (yt-dlp)."

    async def run(self, context: TaskContext) -> TaskResult:
        dry = bool(context.metadata.get("dry_run", False))
        try:
            bvid = _bvid(context.metadata)
            out = job_dir(context.metadata, bvid)
            result = download_best(bvid, out, dry_run=dry)
            if not dry:
                save_manifest(manifest_path(context.metadata, bvid), {"download": result, "stage": "downloaded"})
        except Exception as exc:
            return TaskResult.failure(str(exc))
        return TaskResult.ok("downloaded" if not dry else "would_download", **result)


class _BriefTask(Task):
    name = "bili_yt.brief"
    description = "Write editable YouTube brief (template or LLM script)."

    async def run(self, context: TaskContext) -> TaskResult:
        try:
            bvid = _bvid(context.metadata)
            man_path = manifest_path(context.metadata, bvid)
            if man_path.is_file():
                download = load_manifest(man_path).get("download") or {}
            else:
                download = {
                    "bvid": bvid,
                    "title": str(context.metadata.get("title") or bvid),
                    "url": f"https://www.bilibili.com/video/{bvid}",
                    "description": str(context.metadata.get("description") or ""),
                }
            content = build_brief_payload(download, context.metadata)
            path = brief_path(context.metadata, bvid)
            dry = bool(context.metadata.get("dry_run", False))
            if not dry:
                write_brief(path, content)
                if man_path.is_file():
                    man = load_manifest(man_path)
                    man["stage"] = "brief_ready"
                    man["brief_path"] = str(path)
                    save_manifest(man_path, man)
        except Exception as exc:
            return TaskResult.failure(str(exc))
        return TaskResult.ok(
            "brief_written" if not dry else "would_write_brief",
            bvid=bvid,
            brief_path=str(path),
            preview=content[:500],
            dry_run=dry,
            hint="Edit brief.md, then set confirmed=true or create CONFIRMED file",
        )


class _ConfirmStatusTask(Task):
    name = "bili_yt.confirm_status"
    description = "Check whether user confirmed the brief for upload."

    async def run(self, context: TaskContext) -> TaskResult:
        try:
            bvid = _bvid(context.metadata)
            confirmed_flag = bool(context.metadata.get("confirmed", False))
            conf_file = confirm_path(context.metadata, bvid).is_file()
            confirmed = confirmed_flag or conf_file
            bpath = brief_path(context.metadata, bvid)
            brief_exists = bpath.is_file()
        except Exception as exc:
            return TaskResult.failure(str(exc))
        return TaskResult.ok(
            "confirmed" if confirmed else "waiting_for_confirmation",
            bvid=bvid,
            confirmed=confirmed,
            brief_exists=brief_exists,
            brief_path=str(bpath),
            confirm_file=str(confirm_path(context.metadata, bvid)),
        )


class _ConfirmTask(Task):
    name = "bili_yt.confirm"
    description = "Mark job as confirmed (writes CONFIRMED file)."

    async def run(self, context: TaskContext) -> TaskResult:
        dry = bool(context.metadata.get("dry_run", False))
        try:
            bvid = _bvid(context.metadata)
            path = confirm_path(context.metadata, bvid)
            if not dry:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("confirmed\n", encoding="utf-8")
                man_path = manifest_path(context.metadata, bvid)
                if man_path.is_file():
                    man = load_manifest(man_path)
                    man["stage"] = "confirmed"
                    save_manifest(man_path, man)
        except Exception as exc:
            return TaskResult.failure(str(exc))
        return TaskResult.ok("confirmed" if not dry else "would_confirm", bvid=bvid, path=str(path))


class _UploadTask(Task):
    name = "bili_yt.upload"
    description = "Upload to YouTube only after confirmation (private by default)."

    async def run(self, context: TaskContext) -> TaskResult:
        dry = bool(context.metadata.get("dry_run", True))
        try:
            bvid = _bvid(context.metadata)
            confirmed = bool(context.metadata.get("confirmed", False)) or confirm_path(
                context.metadata, bvid
            ).is_file()
            if not confirmed and not dry:
                return TaskResult.failure(
                    "not confirmed — edit brief, then bili_yt.confirm or metadata.confirmed=true",
                    bvid=bvid,
                )
            man_file = manifest_path(context.metadata, bvid)
            man = load_manifest(man_file) if man_file.is_file() else {}
            download = man.get("download") or {}
            bpath = brief_path(context.metadata, bvid)
            if bpath.is_file():
                sections = parse_brief_sections(read_brief(bpath))
            else:
                sections = {
                    "title": str(download.get("title") or bvid),
                    "description": str(download.get("description") or ""),
                    "tags": "bilibili",
                }
            tags = [t.strip() for t in sections.get("tags", "").replace(",", "\n").splitlines() if t.strip()]
            result = upload_video(
                video_path=str(download.get("video_path") or context.metadata.get("video_path") or ""),
                cover_path=str(download.get("cover_path") or context.metadata.get("cover_path") or ""),
                title=sections.get("title") or str(download.get("title") or bvid),
                description=sections.get("description") or "",
                tags=tags or ["bilibili"],
                dry_run=dry,
                client_secrets=str(context.metadata.get("youtube_client_secrets") or "") or None,
            )
            if not dry and man:
                man["stage"] = "uploaded"
                man["youtube"] = result
                save_manifest(man_file, man)
        except Exception as exc:
            return TaskResult.failure(str(exc))
        return TaskResult.ok("uploaded" if result.get("uploaded") else "upload_planned", bvid=bvid, **result)


class _RunPipelineTask(Task):
    name = "bili_yt.run"
    description = "Pipeline: download → brief → wait confirmation (stops before upload unless confirmed)."

    async def run(self, context: TaskContext) -> TaskResult:
        meta = dict(context.metadata)
        dry = bool(meta.get("dry_run", False))
        results: dict = {}
        try:
            bvid = _bvid(meta)
            if not meta.get("skip_download"):
                dl = await _DownloadTask().run(TaskContext(run_id=context.run_id, metadata=meta))
                if not dl.success:
                    return dl
                results["download"] = dl.data
            brief = await _BriefTask().run(TaskContext(run_id=context.run_id, metadata=meta))
            if not brief.success:
                return brief
            results["brief"] = brief.data
            status = await _ConfirmStatusTask().run(TaskContext(run_id=context.run_id, metadata=meta))
            results["confirm"] = status.data
            if status.data.get("confirmed"):
                up_meta = {**meta, "dry_run": dry if "dry_run" in meta else True}
                up = await _UploadTask().run(TaskContext(run_id=context.run_id, metadata=up_meta))
                results["upload"] = up.data
                if not up.success:
                    return TaskResult.failure(up.message, **results)
                return TaskResult.ok("pipeline_complete", bvid=bvid, **results)
            return TaskResult.ok(
                "awaiting_confirmation",
                bvid=bvid,
                next_steps=[
                    f"Edit {brief.data.get('brief_path')}",
                    "Run bili_yt.confirm or pass confirmed=true",
                    "Run bili_yt.upload with dry_run=false and youtube_client_secrets",
                ],
                **results,
            )
        except Exception as exc:
            return TaskResult.failure(str(exc), **results)


class BiliToYoutubePlugin(Plugin):
    metadata = PluginMetadata(
        name="bili_to_youtube",
        version="0.1.0",
        description="Bilibili VOD highest quality + cover → editable LLM/template brief → confirm → YouTube.",
        tags=["bilibili", "youtube", "workflow"],
    )

    def tasks(self) -> list[Task]:
        return [
            _DownloadTask(),
            _BriefTask(),
            _ConfirmStatusTask(),
            _ConfirmTask(),
            _UploadTask(),
            _RunPipelineTask(),
        ]
