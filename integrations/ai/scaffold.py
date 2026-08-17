"""Plugin scaffold: template (offline) or LLM-assisted (when AI key set)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from integrations.ai.client import AiClientError, OpenAICompatibleClient
from integrations.ai.context import load_doc_pack, repo_root
from integrations.ai.filespec import FileSpec, apply_files, parse_file_blocks, validate_package_paths

NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(slots=True)
class ScaffoldResult:
    plugin_name: str
    mode: str  # template | llm
    dry_run: bool
    files: list[dict[str, str]]
    errors: list[str]
    raw_model_text: str | None = None


def _pascal(name: str) -> str:
    return "".join(p.capitalize() for p in name.split("_"))


def template_files(plugin_name: str, *, description: str = "") -> list[FileSpec]:
    cls = f"{_pascal(plugin_name)}Plugin"
    task_name = f"{plugin_name}.run"
    desc = description or f"{plugin_name} automation plugin"
    yaml = f"""name: {plugin_name}
version: 0.1.0
category: business
entrypoint:
  module: packages.{plugin_name}.{plugin_name}.plugin
  class: {cls}
permissions:
  - task.execute
dependencies: []
"""
    init = f'"""{plugin_name} plugin package."""\n'
    plugin_py = f'''from __future__ import annotations

from core.plugin.base import Plugin, PluginMetadata
from core.task.base import Task, TaskContext, TaskResult


class _RunTask(Task):
    name = "{task_name}"
    description = "{desc}"

    async def run(self, context: TaskContext) -> TaskResult:
        dry_run = bool(context.metadata.get("dry_run", True))
        return TaskResult.ok(
            "completed",
            plugin="{plugin_name}",
            dry_run=dry_run,
            metadata_keys=sorted(context.metadata.keys()),
        )


class {cls}(Plugin):
    metadata = PluginMetadata(
        name="{plugin_name}",
        version="0.1.0",
        description="{desc}",
        tags=["{plugin_name}"],
    )

    def tasks(self) -> list[Task]:
        return [_RunTask()]
'''
    base = f"packages/{plugin_name}"
    return [
        FileSpec(f"{base}/plugin.yaml", yaml if yaml.endswith("\n") else yaml + "\n"),
        FileSpec(f"{base}/{plugin_name}/__init__.py", init),
        FileSpec(
            f"{base}/{plugin_name}/plugin.py",
            plugin_py if plugin_py.endswith("\n") else plugin_py + "\n",
        ),
    ]


def scaffold_plugin(
    *,
    name: str,
    brief: str = "",
    dry_run: bool = True,
    use_llm: bool = False,
    root: Path | None = None,
) -> ScaffoldResult:
    plugin_name = name.strip().lower().replace("-", "_")
    errors: list[str] = []
    if not NAME_RE.match(plugin_name):
        return ScaffoldResult(plugin_name, "invalid", dry_run, [], ["invalid plugin name"])

    root = root or repo_root()
    raw: str | None = None
    mode = "template"

    if use_llm:
        client = OpenAICompatibleClient()
        if not client.enabled:
            errors.append("use_llm requested but SWP_AI_API_KEY is not set; falling back to template")
            files = template_files(plugin_name, description=brief)
        else:
            mode = "llm"
            system = (
                "You are the SWP plugin author. Follow the contract exactly. "
                "Output only ### FILE blocks under packages/<name>/.\n\n" + load_doc_pack()
            )
            user = (
                f"Plugin name: {plugin_name}\n"
                f"Brief: {brief or 'generic automation plugin'}\n"
                "Generate plugin.yaml, __init__.py, and plugin.py."
            )
            try:
                raw = client.chat(system=system, user=user)
                files = parse_file_blocks(raw)
                if not files:
                    errors.append("LLM returned no FILE blocks; using template")
                    files = template_files(plugin_name, description=brief)
                    mode = "template"
            except AiClientError as exc:
                errors.append(str(exc))
                files = template_files(plugin_name, description=brief)
                mode = "template"
    else:
        files = template_files(plugin_name, description=brief)

    path_errors = validate_package_paths(files, plugin_name=plugin_name)
    errors.extend(path_errors)
    if path_errors:
        return ScaffoldResult(plugin_name, mode, dry_run, [], errors, raw)

    written = apply_files(files, root=root, dry_run=dry_run)
    return ScaffoldResult(plugin_name, mode, dry_run, written, errors, raw)
