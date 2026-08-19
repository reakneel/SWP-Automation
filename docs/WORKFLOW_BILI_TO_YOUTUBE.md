# Workflow: Bilibili \u2192 YouTube (confirm before upload)

**Only republish content you have rights to.** Respect Bilibili and YouTube terms and copyright.

## Pipeline

```text
bili_yt.download   \u2192  best video + cover (yt-dlp)
bili_yt.brief      \u2192  editable brief.md (template or LLM script)
                   \u2192  USER EDITS + CONFIRMS
bili_yt.confirm    \u2192  writes CONFIRMED
bili_yt.upload     \u2192  YouTube (private by default; dry_run default true)
```

Or: `bili_yt.run` \u2192 download + brief \u2192 stops at awaiting_confirmation.

## Install

```bash
pip install -e ".[dev]"
pip install yt-dlp
# real upload: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

## Example

```python
meta = {
    "bvid": "BVxxxxxxxx",
    "work_dir": "data/bili_to_youtube",
    "brief_template_path": "templates/bili_to_youtube/brief.md.j2",
    "use_llm": False,
    "llm_script_path": "templates/bili_to_youtube/llm_script.txt",
}
await rt.executor.execute("bili_yt.run", meta)
# edit data/bili_to_youtube/<BVid>/brief.md
await rt.executor.execute("bili_yt.confirm", meta)
await rt.executor.execute("bili_yt.upload", {**meta, "dry_run": True})
```

Upload refuses real publish without confirmation when dry_run=false.
Quality: yt-dlp bestvideo*+bestaudio/best + thumbnail.
