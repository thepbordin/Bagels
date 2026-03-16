---
phase: quick
plan: 2
subsystem: managers
tags: [bugfix, config, lazy-import, startup]
dependency_graph:
  requires: []
  provides: [lazy-CONFIG-access-accounts, lazy-CONFIG-access-utils]
  affects: [bagels.managers.accounts, bagels.managers.utils]
tech_stack:
  added: []
  patterns: [lazy-module-reference]
key_files:
  created: []
  modified:
    - src/bagels/managers/accounts.py
    - src/bagels/managers/utils.py
decisions:
  - "Use module-level `import bagels.config as config_mod` and access config_mod.CONFIG at call time, matching the pattern already used by all other managers"
metrics:
  duration: "~5 min"
  completed: "2026-03-17"
  tasks_completed: 2
  files_modified: 2
---

# Quick Task 2: Fix AttributeError CONFIG is None on --at Startup Summary

**One-liner:** Replaced eager `from bagels.config import CONFIG` with lazy `import bagels.config as config_mod` in accounts.py and utils.py so CONFIG is resolved at call time after load_config() runs.

## What Was Done

The `--at` flag invokes `set_custom_root` before `load_config()`. Both `accounts.py` and `utils.py` had `from bagels.config import CONFIG` at module level, which bound `CONFIG = None` as a fixed name. When account-balance functions were called during `RecordTemplateForm` initialization, they dereferenced `None.defaults.round_decimals` and raised `AttributeError`.

All other managers already used the lazy pattern (`import bagels.config as config_mod`, access `config_mod.CONFIG` at call time). This fix applies the same pattern to the two remaining offenders.

## Tasks Completed

| Task | Description | Commit | Status |
|------|-------------|--------|--------|
| 1 | Fix lazy CONFIG access in accounts.py and utils.py | 1da59b5 | Done |
| 2 | Smoke test --at flag startup | 1da59b5 | Done (verification only, no files changed) |

## Changes

### src/bagels/managers/accounts.py

- Line 8: `from bagels.config import CONFIG` -> `import bagels.config as config_mod`
- Line 140: `CONFIG.defaults.round_decimals` -> `config_mod.CONFIG.defaults.round_decimals`

### src/bagels/managers/utils.py

- Line 8: `from bagels.config import CONFIG` -> `import bagels.config as config_mod`
- Line 59: `CONFIG.defaults.first_day_of_week` -> `config_mod.CONFIG.defaults.first_day_of_week`
- Line 167: `CONFIG.defaults.round_decimals` -> `config_mod.CONFIG.defaults.round_decimals`
- Line 185: `CONFIG.defaults.round_decimals` -> `config_mod.CONFIG.defaults.round_decimals`
- Lines 215-217: Three `CONFIG.state.budgeting.*` accesses -> `config_mod.CONFIG.state.budgeting.*`

## Verification

- `import bagels.managers.accounts; import bagels.managers.utils` -> exits 0, "imports OK"
- `from bagels.config import load_config; load_config(); from bagels.managers.accounts import get_account_balance` -> exits 0, "OK"
- `grep "from bagels.config import CONFIG" accounts.py utils.py` -> no results (exit 1)
- `grep "config_mod.CONFIG" accounts.py utils.py` -> 9 matches covering all former CONFIG usage sites

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- [x] src/bagels/managers/accounts.py modified and committed (1da59b5)
- [x] src/bagels/managers/utils.py modified and committed (1da59b5)
- [x] No bare `CONFIG` references remain in either file
- [x] All config_mod.CONFIG references verified via grep
