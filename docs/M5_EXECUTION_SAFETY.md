# M5.5 Execution Safety

Hardens plugin loading and task execution after dynamic discovery (M5.4).

## Entrypoint allowlist

Only modules under configured prefixes may be imported from `plugin.yaml`.

- Default: `modules.`
- Override: `SWP_PLUGIN_MODULE_PREFIXES` (list)

Rejected examples: `os`, `subprocess`, absolute paths, modules outside the allowlist.

## Permissions

Manifest field `permissions` is validated at load time.

| Permission     | Meaning                                      |
|----------------|----------------------------------------------|
| `task.execute` | Register and run tasks (default if omitted)  |
| `net.http`     | Outbound HTTP (declared intent)              |
| `fs.read`      | Filesystem read (declared intent)            |
| `fs.write`     | Filesystem write (declared intent)           |
| `notify`       | Platform notification boundary               |

- Empty permissions → default `["task.execute"]`
- `SWP_PLUGIN_STRICT_PERMISSIONS=true` rejects unknown permission strings

Deep OS/network sandboxing is out of scope; M5.5 enforces boundaries at load/execute time only.

## Executor timeout

`TaskExecutor.execute` wraps `task.run` with `asyncio.wait_for`.

- Default: `SWP_EXECUTION_TIMEOUT_SECONDS` (300)
- On timeout: `ExecutionStatus.FAILED`, error `task timed out after Ns`

## Batch load isolation

`PluginManager.load_from_paths` / `load_from_paths_report`:

- One failed plugin does not abort the batch
- Failures recorded as `(name_or_path, error)` and `PluginState.FAILED`
- Successful plugins still reach `INITIALIZED`

## Metadata guardrails

- Max keys: `SWP_METADATA_MAX_KEYS` (64)
- Max value length: `SWP_METADATA_MAX_VALUE_LENGTH` (4096)
- Invalid metadata fails the run without calling the task
