# Plugin Author Agent

Developer aid to scaffold and validate SWP package plugins.

## Components

| Piece | Path |
|-------|------|
| AI contract | `docs/PLUGIN_AI_CONTRACT.md` |
| OpenAI-compatible client | `integrations/ai/client.py` |
| Doc pack loader | `integrations/ai/context.py` |
| FILE block parse/apply | `integrations/ai/filespec.py` |
| Scaffold | `integrations/ai/scaffold.py` |
| Check | `integrations/ai/check.py` |
| CLI | `automation plugin …` |
| Skill | `skills/plugin-author/SKILL.md` |

## Settings

| Env | Purpose |
|-----|---------|
| `SWP_AI_API_KEY` | Enables `--llm` path |
| `SWP_AI_BASE_URL` | Default `https://api.x.ai/v1` |
| `SWP_AI_MODEL` | Default model id |

## Flow

```text
brief → scaffold (template or LLM)
      → dry-run file list
      → --write packages/<name>/
      → plugin check
      → human review / tests
```
