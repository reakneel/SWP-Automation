from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from core.migration.cli import migrate_inventory, validate_inventory
from core.migration.pipeline import MigrationPipeline
from core.task.registry import TaskRegistry
from core.worker.executor import TaskExecutor
from modules.daily.example import ExampleHelloTask

app = typer.Typer(help="SWP Automation command line interface")


def build_registry() -> TaskRegistry:
    registry = TaskRegistry()
    registry.register(ExampleHelloTask())
    return registry


task_app = typer.Typer(help="Manage automation tasks")
app.add_typer(task_app, name="task")

migration_app = typer.Typer(help="Inspect and migrate legacy automation projects")
app.add_typer(migration_app, name="migration")


@task_app.command("list")
def list_tasks() -> None:
    """List registered tasks."""
    for task in build_registry().list():
        typer.echo(f"{task.name}\t{task.description}")


@task_app.command("run")
def run_task(name: str) -> None:
    """Run a registered task immediately."""
    result = asyncio.run(TaskExecutor(build_registry()).execute(name))
    if result.success:
        typer.echo(result.message)
        return
    typer.echo(f"Task failed: {result.message}", err=True)
    raise typer.Exit(code=1)


@migration_app.command("scan")
def scan_migration(
    source: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),  # noqa: B008
    output: Path = typer.Option(Path("migration"), "--output", "-o"),  # noqa: B008
) -> None:
    """Scan a legacy project without importing or executing it."""
    items = MigrationPipeline().export(source, output)
    typer.echo(f"Discovered {len(items)} migration items")
    typer.echo(f"Inventory: {output / 'migration-inventory.json'}")
    typer.echo(f"Report: {output / 'migration-report.md'}")


@migration_app.command("generate")
def generate_migration(
    source: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),  # noqa: B008
    output: Path = typer.Option(Path("plugins"), "--output", "-o"),  # noqa: B008
) -> None:
    """Generate reviewable, disabled adapters from an inventory JSON file."""
    generated = migrate_inventory(source, output)
    typer.echo(f"Generated {len(generated)} reviewable adapters")
    for path in generated:
        typer.echo(path)


@migration_app.command("validate")
def validate_migration(
    inventory: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),  # noqa: B008
    source: Path = typer.Option(Path("."), "--source", "-s"),  # noqa: B008
) -> None:
    """Validate inventory readiness without importing or executing legacy code."""
    errors = validate_inventory(inventory, source)
    if errors:
        for error in errors:
            typer.echo(error, err=True)
        raise typer.Exit(code=1)
    typer.echo("Migration inventory is ready")


@migration_app.command("migrate")
def migrate_migration(
    inventory: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),  # noqa: B008
    output: Path = typer.Option(Path("plugins"), "--output", "-o"),  # noqa: B008
) -> None:
    """Generate disabled adapters from an inventory for human review."""
    generated = migrate_inventory(inventory, output)
    typer.echo(f"Generated {len(generated)} disabled adapters")
    typer.echo("Review and wire legacy callables before enabling them")


plugin_app = typer.Typer(help="Scaffold and check package plugins (optional AI)")
app.add_typer(plugin_app, name="plugin")


@plugin_app.command("docs")
def plugin_docs() -> None:
    """List plugin authoring documents used by the agent."""
    from integrations.ai.context import list_plugin_docs

    for item in list_plugin_docs():
        typer.echo(f"{item['path']}\texists={item['exists']}\tbytes={item['bytes']}")


@plugin_app.command("check")
def plugin_check(
    path: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),  # noqa: B008
) -> None:
    """Validate a package plugin directory (yaml, permissions, entrypoint class)."""
    from integrations.ai.check import check_plugin_package

    result = check_plugin_package(path)
    for w in result.warnings:
        typer.echo(f"warning: {w}")
    if result.errors:
        for e in result.errors:
            typer.echo(f"error: {e}", err=True)
        raise typer.Exit(code=1)
    typer.echo(f"ok\t{result.info.get('name')}\t{result.path}")


@plugin_app.command("scaffold")
def plugin_scaffold(
    name: str = typer.Argument(..., help="Plugin package name (snake_case)"),
    brief: str = typer.Option("", "--brief", "-b", help="Short description / intent"),
    write: bool = typer.Option(False, "--write", help="Write files (default is dry-run)"),
    llm: bool = typer.Option(False, "--llm", help="Use OpenAI-compatible LLM when SWP_AI_API_KEY is set"),
) -> None:
    """Scaffold a package plugin (template offline; optional --llm)."""
    from integrations.ai.scaffold import scaffold_plugin

    result = scaffold_plugin(name=name, brief=brief, dry_run=not write, use_llm=llm)
    typer.echo(f"plugin={result.plugin_name}\tmode={result.mode}\tdry_run={result.dry_run}")
    for err in result.errors:
        typer.echo(f"note: {err}", err=True)
    for f in result.files:
        typer.echo(f"{f['action']}\t{f['path']}\t{f['bytes']}B")
    if result.errors and not result.files:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
