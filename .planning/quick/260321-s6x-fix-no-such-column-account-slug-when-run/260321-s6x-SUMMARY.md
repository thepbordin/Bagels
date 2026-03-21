---
phase: quick
plan: 260321-s6x
status: completed
completed: 2026-03-21
summary_type: quick-task
---

# Quick Task 260321-s6x Summary

## Task
fix no such column account.slug when running with --at instance

## Outcome
Resolved the `--at` startup crash by rebinding already-imported manager `Session` factories whenever the active SQLAlchemy engine is reconnected to a new custom-root database.

## Changes Made
- Updated `src/bagels/models/database/app.py`:
  - Added `_rebind_loaded_sessionmakers(new_engine)`.
  - `_ensure_engine_current()` now rebinds loaded manager modules after switching engine.
- Added regression test `tests/integration/test_custom_root_session_rebind.py`:
  - Simulates pre-imported manager module + custom root switch.
  - Verifies Session bind URL points to the custom DB.
  - Verifies query executes without OperationalError.

## Verification
- `uv run pytest tests/integration/test_custom_root_session_rebind.py -q` → `1 passed`
- Reproduction script (pre-import manager then set custom root + `init_db()`) shows manager bind URL points to `instance/db.db` and query succeeds.
- Live smoke run: `uv run bagels --at ./instance` opened Home UI and no `account.slug` traceback appeared.

## Notes
- This fix specifically addresses stale Session bindings caused by module import timing in `__main__` command wiring.
