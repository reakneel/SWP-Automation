# Skill + plugin dual path

SWP keeps **plugins** as the execution source of truth and optional **skills** as an LLM-facing adapter.

## Rule

| Context | Path | Needs `SWP_AI_API_KEY`? |
|---------|------|-------------------------|
| Scheduler, worker, CLI, CI | Plugin tasks | No |
| Agent / chat with tools | Skill → same core / plugin | Yes (gate) |

```text
Domain core  ←──  Plugin tasks  ←──  local automation
     ↑
     └──  Skill scripts / tool schema  ←──  agent (key required)
```

## Settings

| Env | Purpose |
|-----|---------|
| `SWP_AI_API_KEY` | Enables agent skill path (`integrations.ai.gate.ai_enabled`) |
| `SWP_AI_BASE_URL` | Default `https://api.x.ai/v1` (OpenAI-compatible) |
| `SWP_AI_MODEL` | Default model id |

Empty API key ⇒ skills should refuse agent-only mode; plugins still work.

## Example: bili-live

- Plugin: `packages/bili_live_rec`
- Skill: `skills/bili-live/SKILL.md`
- Runner: `skills/bili-live/scripts/run_tool.py` (invokes plugin tasks)

```bash
python skills/bili-live/scripts/run_tool.py room_check --room 6 --require-ai-key
```
