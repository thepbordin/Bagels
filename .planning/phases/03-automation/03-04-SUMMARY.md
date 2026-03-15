---
phase: 03-automation
plan: "04"
subsystem: startup-sync
tags: [tdd, textual, worker, importer, git, data-sync]
dependency_graph:
  requires: ["03-01", "03-02"]
  provides: ["DATA-08", "GIT-08"]
  affects: ["src/bagels/app.py", "src/bagels/importer/importer.py"]
tech_stack:
  added: ["textual @work decorator (thread=True, exclusive=True)"]
  patterns: ["TDD red-green", "background worker", "lazy imports inside worker", "swallowed exceptions"]
key_files:
  created: ["tests/automation/test_startup.py"]
  modified: ["src/bagels/app.py", "src/bagels/importer/importer.py"]
decisions:
  - "Added run_full_import() as public entry point on importer.py — orchestrates all entity imports in dependency order"
  - "Tests access __wrapped__ attribute of @work-decorated method to invoke raw logic without Textual runtime"
  - "Used patch.object with PropertyMock for self.app since Textual App.app is a read-only property"
  - "Worker uses lazy imports (inside function body) so mocking targets bagels.importer.importer.run_full_import directly"
metrics:
  duration: "13 min"
  completed: "2026-03-16"
  tasks_completed: 2
  files_changed: 3
---

# Phase 3 Plan 04: Startup Import Worker Summary

**One-liner:** Non-blocking Textual @work(thread=True) startup worker in app.py that optionally git-pulls then imports all YAML files to SQLite on every TUI launch.

## What Was Built

### run_full_import() — importer.py

A top-level orchestrator function added to `src/bagels/importer/importer.py` that:
- Opens a SQLAlchemy session from `db_engine`
- Reads `accounts.yaml`, `categories.yaml`, `persons.yaml`, `templates.yaml` from `data_directory()`
- Reads all `records/YYYY-MM.yaml` monthly files in sorted order
- Calls the existing entity-level import functions for each present file
- Silently skips missing files
- Closes the session in a `finally` block

### run_startup_import() — app.py

A `@work(thread=True, exclusive=True)` method on the `App` class:
- Called from `on_mount` (non-blocking — TUI renders immediately)
- Lazy-imports `CONFIG` and returns early if `None` (test-safe)
- Optionally calls `pull_from_remote(silent=True)` if `CONFIG.git.enabled and CONFIG.git.auto_pull`
- Pull failures are caught and ignored — startup import proceeds regardless
- Calls `run_full_import()` then fires a transient `notify()` toast via `call_from_thread`
- Outer `except Exception: pass` ensures any crash is swallowed — TUI never dies from import failure

## Tests — tests/automation/test_startup.py

8 unit tests verifying all behaviors:

| Test | Coverage |
|------|----------|
| 1 | `run_full_import` called exactly once |
| 2 | `auto_pull=True` triggers pull before import (ordering verified) |
| 3 | `auto_pull=False` skips pull entirely |
| 4 | `git.enabled=False` skips pull even if `auto_pull=True` |
| 5 | Pull exception does not block import |
| 6 | Import exception is swallowed (TUI never crashes) |
| 7 | `on_mount` source calls `run_startup_import()` |
| 8 | `CONFIG=None` returns early without calling import |

Tests bypass the Textual runtime by calling `App.run_startup_import.__wrapped__(instance)` directly, using `patch.object` with `PropertyMock` to handle the read-only `app` property.

## Deviations from Plan

### Auto-added Features

**1. [Rule 2 - Missing Functionality] Added run_full_import() as new public function**
- **Found during:** Step 1 (check importer entry point)
- **Issue:** `importer.py` had no top-level `run_full_import()` function — only entity-specific import functions. The plan assumed one would exist.
- **Fix:** Created `run_full_import()` that orchestrates all entity imports in correct dependency order (accounts → categories → persons → templates → records)
- **Files modified:** `src/bagels/importer/importer.py`
- **Commit:** 4771f69

**2. [Rule 1 - Bug] Fixed test approach for Textual App.app property**
- **Found during:** Test GREEN phase execution
- **Issue:** `App.app` is a read-only property in Textual — `instance.app = MagicMock()` raised `AttributeError`
- **Fix:** Used `patch.object(type(instance), "app", new_callable=PropertyMock)` to mock the property; mocked `call_from_thread` directly on instance (Textual App self.app returns self)
- **Files modified:** `tests/automation/test_startup.py`
- **Commit:** 4771f69

## Self-Check: PASSED

- `src/bagels/app.py` has `run_startup_import` method with `@work` decorator: FOUND
- `src/bagels/importer/importer.py` has `run_full_import()` function: FOUND
- `tests/automation/test_startup.py` has 8 tests: FOUND
- Commit 4771f69: FOUND
- All 8 tests pass: CONFIRMED
