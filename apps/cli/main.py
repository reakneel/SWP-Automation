from __future__ import annotations

import asyncio
from pathlib import Path

import typer

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
    source: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    output: Path = typer.Option(Path("migration"), "--output", "-o"),
) -> None:
    """Scan a legacy project without importing or executing it."""
    items = MigrationPipeline().export(source, output)
    typer.echo(f"Discovered {len(items)} migration items")
    typer.echo(f"Inventory: {output / 'migration-inventory.json'}")
    typer.echo(f"Report: {output / 'migration-report.md'}")


@migration_app.command("generate")
def generate_migration(
    source: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    output: Path = typer.Option(Path("plugins"), "--output", "-o"),
) -> None:
    """Generate reviewable, disabled adapters from an inventory JSON file."""
    import json

    from core.migration.inventory import (
        InventoryItem,
        MigrationCategory,
        MigrationStatus,
    )

    raw_items = json.loads(source.read_text(encoding="utf-8"))
    items = [
        InventoryItem(
            name=item["name"],
            source=item["source"],
            entrypoint=item.get("entrypoint"),
            category=MigrationCategory(item.get("category", "unknown")),
            status=MigrationStatus(item.get("status", "discovered")),
            schedule=item.get("schedule"),
            side_effects=item.get("side_effects", []),
            dependencies=item.get("dependencies", []),
            notes=item.get("notes", ""),
            metadata=item.get("metadata", {}),
        )
        for item in raw_items
    ]
    generated = MigrationPipeline().generate_adapters(items, output)
    typer.echo(f"Generated {len(generated)} reviewable adapters")
    for path in generated:
        typer.echo(path)


if __name__ == "__main__":
    app()
