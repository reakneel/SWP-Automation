# OpenClaw integration

OpenClaw is an integration layer, not a dependency of `core/`.

## Exposed operations

- `automation.list_tasks`
- `automation.run_task`
- `automation.get_run`
- `automation.health`

## Safety rules

1. Only registered task names may be executed.
2. The adapter must not contain business logic.
3. Secrets belong in environment/configuration, never in task manifests.
4. Prefer read-only discovery before execution.
5. Long-running work should use scheduler/worker facilities rather than blocking the adapter.

The exact OpenClaw transport/registration mechanism is intentionally kept outside this repository's core contract so it can evolve independently of the automation runtime.
