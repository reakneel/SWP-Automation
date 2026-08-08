from core.task.base import Task, TaskContext, TaskResult


class ExampleHelloTask(Task):
    name = "example.hello"
    description = "Example task used to validate the automation core."

    async def run(self, context: TaskContext) -> TaskResult:
        return TaskResult.ok("automation core is running", run_id=context.run_id)
