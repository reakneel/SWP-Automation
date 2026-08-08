from __future__ import annotations

import asyncio

import typer

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


if __name__ == "__main__":
    app()
