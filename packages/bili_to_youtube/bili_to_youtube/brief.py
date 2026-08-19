"""Editable brief script: template + optional LLM, user can modify file before confirm."""
from __future__ import annotations

from pathlib import Path
from typing import Any

DEFAULT_TEMPLATE = """# YouTube brief (edit this file, then confirm)

## Title
{title}

## Description
{description}

## Tags
{tags}

## Notes
- Source: {source_url}
- BVid: {bvid}
- Generated: template
- Edit freely. Set metadata.confirmed=true or create CONFIRMED file to proceed upload.
"""


def render_template(
    *,
    title: str,
    description: str,
    tags: str,
    source_url: str,
    bvid: str,
    template_text: str | None = None,
) -> str:
    tpl = template_text or DEFAULT_TEMPLATE
    return tpl.format(
        title=title or "",
        description=description or "",
        tags=tags or "",
        source_url=source_url or "",
        bvid=bvid or "",
    )


def write_brief(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_brief(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_brief_sections(text: str) -> dict[str, str]:
    sections = {"title": "", "description": "", "tags": ""}
    current = None
    buf: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current and current in sections:
                sections[current] = "\n".join(buf).strip()
            name = line[3:].strip().lower()
            current = {"title": "title", "description": "description", "tags": "tags"}.get(name)
            buf = []
        else:
            if current:
                buf.append(line)
    if current and current in sections:
        sections[current] = "\n".join(buf).strip()
    return sections


def generate_with_llm(
    *,
    title: str,
    source_description: str,
    bvid: str,
    source_url: str,
    user_script: str | None = None,
) -> str | None:
    try:
        from integrations.ai.client import AiClientError, OpenAICompatibleClient
    except ImportError:
        return None
    client = OpenAICompatibleClient()
    if not client.enabled:
        return None
    system = user_script or (
        "You write short YouTube titles and descriptions for reuploads. "
        "Output markdown with ## Title, ## Description, ## Tags only. "
        "Keep description under 2000 chars. Do not invent copyright ownership claims."
    )
    user = (
        f"Original title: {title}\n"
        f"BVid: {bvid}\n"
        f"URL: {source_url}\n"
        f"Original description:\n{source_description[:3000]}\n"
    )
    try:
        return client.chat(system=system, user=user, temperature=0.4)
    except AiClientError:
        return None


def build_brief_payload(download: dict[str, Any], meta: dict[str, Any]) -> str:
    bvid = str(download.get("bvid") or "")
    title = str(download.get("title") or bvid)
    source_url = str(download.get("url") or "")
    source_desc = str(download.get("description") or "")
    tags = str(meta.get("tags") or "bilibili, repost")
    template_path = meta.get("brief_template_path")
    template_text = None
    if template_path:
        p = Path(str(template_path))
        if p.is_file():
            template_text = p.read_text(encoding="utf-8")

    use_llm = bool(meta.get("use_llm", False))
    user_script = None
    script_path = meta.get("llm_script_path")
    if script_path and Path(str(script_path)).is_file():
        user_script = Path(str(script_path)).read_text(encoding="utf-8")

    if use_llm:
        llm_out = generate_with_llm(
            title=title,
            source_description=source_desc,
            bvid=bvid,
            source_url=source_url,
            user_script=user_script,
        )
        if llm_out:
            return llm_out

    return render_template(
        title=title,
        description=source_desc[:2000] or f"Source: {source_url}",
        tags=tags,
        source_url=source_url,
        bvid=bvid,
        template_text=template_text,
    )
