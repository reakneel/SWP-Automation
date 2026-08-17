# Plugin: bili_live_rec

Split of the standalone `blrec.py` script into a SWP package plugin.

## Why split

| Module | Responsibility |
|--------|----------------|
| `wbi.py` | Anonymous `buvid3` + WBI sign |
| `room.py` | Room info + stream URL (play-gateway / getRoomPlayInfo) |
| `recorder.py` | **Asyncio** ffmpeg segment (stoppable) |
| `plugin.py` | SWP tasks |

## Subprocess fix

Original script used `subprocess.run(...)`, which:

- Blocks the whole thread until ffmpeg exits
- Handles Ctrl+C poorly with multi-thread workers
- Treats stream-end exits as hard errors

`recorder.record_once` uses `asyncio.create_subprocess_exec` + `wait_for(max_seconds)` and **terminates** the process on timeout/cancel so the SWP worker can finish the task.

## Tasks

| Task | Metadata | Notes |
|------|----------|--------|
| `bili.room_check` | `room` | Status only |
| `bili.stream_url` | `room`, `qn?`, `cookie?` | Resolve URL |
| `bili.record_segment` | `room`, `max_seconds?` (default 60, max 600), `output?`, `format?`, `dry_run?` | Bounded record |

Long 24/7 multi-room loops stay **outside** the task executor (use an external supervisor or future daemon). The plugin exposes **safe, time-bounded** units the platform can schedule and audit.

## Example

```python
await runtime.executor.execute("bili.room_check", {"room": "6"})
await runtime.executor.execute("bili.stream_url", {"room": "6", "qn": 10000})
await runtime.executor.execute(
    "bili.record_segment",
    {"room": "6", "max_seconds": 30, "format": "flv", "output": "downloads"},
)
```

Personal use only; respect platform terms and copyright.
