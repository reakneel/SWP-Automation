---
name: plugin-author
description: Scaffold and check SWP package plugins from a brief. Use when the user wants a new plugin, plugin.yaml, Task/Plugin stubs, or validation of packages under packages/. Prefer offline template scaffold; use LLM only when SWP_AI_API_KEY is set and user asks.
---

# Plugin author agent

## Policy

- Execution source of truth remains **plugins**, not the model.
- Default **dry-run** scaffold; only write with explicit `--write` / user confirm.
- Offline path always available (template). `--llm` requires `SWP_AI_API_KEY`.

## Commands

```bash
automation plugin docs
automation plugin scaffold my_tool --brief "poll status page"
automation plugin scaffold my_tool --brief "..." --write
automation plugin scaffold my_tool --brief "..." --llm --write
automation plugin check packages/my_tool
```

## Contract

Follow `docs/PLUGIN_AI_CONTRACT.md` for layout, permissions, and FILE block format.

## Dual path

| Path | When |
|------|------|
| Template scaffold | No key / default |
| LLM scaffold | Key set + `--llm` |
| Plugin check | Always offline |
