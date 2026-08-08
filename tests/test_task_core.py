from core.task.registry import TaskRegistry
from core.worker.executor import TaskExecutor
from modules.daily.example import ExampleHelloTask


async def test_example_task_executes() -> None:
    registry = TaskRegistry()
    registry.register(ExampleHelloTask())

    result = await TaskExecutor(registry).execute("example.hello")

    assert result.success is True
    assert result.data["run_id"]


def test_registry_lists_tasks() -> None:
    registry = TaskRegistry()
    registry.register(ExampleHelloTask())

    assert registry.names() == ["example.hello"]
