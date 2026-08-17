---
name: bili-live
description: Bilibili live room check, stream URL resolve, and bounded segment record via shared plugin core. Use when the user asks about B站直播, bilibili live, room status, stream URL, or recording a short segment. Prefer SWP plugin tasks when no LLM key is needed.
---

# Bilibili live (skill + plugin dual path)

## Policy

- **Local / cron / worker** — call SWP plugin tasks (`bili.*`). No AI key required.
- **Agent session** — use this skill only when `SWP_AI_API_KEY` is set (`integrations.ai.gate.ai_enabled()`).
- **Never** invent ffmpeg loops in the model. Call tools/scripts that wrap the same core as the plugin.

## Shared core

Implementation lives in `packages/bili_live_rec/bili_live_rec/` (wbi, room, recorder).
Plugin tasks and this skill must stay aligned.

| Skill intent | Plugin task | Script |
|--------------|-------------|--------|
| Check room live status | `bili.room_check` | `skills/bili-live/scripts/run_tool.py room_check` |
| Resolve stream URL | `bili.stream_url` | `... run_tool.py stream_url` |
| Record bounded segment | `bili.record_segment` | `... run_tool.py record_segment` |

## Tool rules

1. Require `room` (room id, short id, or live URL).
2. Default `dry_run=true` for `record_segment` unless the user clearly asks to write files.
3. Cap `max_seconds` at 600 (default 60).
4. Optional `cookie` only from user/env — never invent cookies.
5. On failure, return the error message; do not retry unbounded.

## How to run (agent)

```bash
python -c "from integrations.ai.gate import ai_enabled; print(ai_enabled())"

python skills/bili-live/scripts/run_tool.py room_check --room 6
python skills/bili-live/scripts/run_tool.py stream_url --room 6 --qn 10000
python skills/bili-live/scripts/run_tool.py record_segment --room 6 --max-seconds 30 --dry-run
```

Or execute SWP tasks when a runtime is available:

```python
await runtime.executor.execute("bili.room_check", {"room": "6"})
```

## Output

Prefer short JSON for the model — room_id, status, url/qn, or record path/bytes/timed_out.

## References

- Tool JSON schema — `references/tool-schema.json`
- Plugin doc — `docs/PLUGIN_BILI_LIVE_REC.md`
