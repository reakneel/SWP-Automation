# Plugin Template

Copy this template into `modules/<name>/` and rename the classes.

```python
from core.plugin.base import Plugin, PluginMetadata
from core.task.base import Task, TaskContext, TaskResult


class ExampleTask(Task):
    name = "example.run"
    description = "Describe the automation."

    async def run(self, context: TaskContext) -> TaskResult:
        # Call your service/provider here.
        return TaskResult.ok("completed")


class ExamplePlugin(Plugin):
    metadata = PluginMetadata(
        name="example",
        version="0.1.0",
        description="Example plugin",
        tags=["example"],
    )

    def tasks(self) -> list[Task]:
        return [ExampleTask()]
```

For a legacy script, keep the original implementation and put only a thin async adapter in the Task. Migrate internals incrementally after the task is registered and tested.
