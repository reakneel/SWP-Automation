# M4.4 Safe Legacy AST Scanner

The scanner inventories legacy Python code without importing or executing it.

## What it detects

- top-level public functions and async functions
- imported top-level dependencies
- HTTP dependencies
- database/cache dependencies
- notification dependencies
- obvious filesystem/stdout/subprocess side effects

## Safety rule

The scanner uses Python `ast` only. It must not execute legacy code, import legacy modules, evaluate decorators, or run project startup hooks.

## Example

```python
from pathlib import Path
from core.migration.scanner import LegacyScanner

items = LegacyScanner().scan_directory(Path("./legacy"))
```

The resulting `InventoryItem` records can then be classified and wrapped with `LegacyFunctionTask`.

## Deliberate limitations

Static detection is conservative. It should not claim that an unknown function is safe merely because no side effect was detected. Runtime behavior remains the source of truth during migration tests.
