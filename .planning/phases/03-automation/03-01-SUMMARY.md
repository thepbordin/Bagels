---
phase: 03-automation
plan: "01"
subsystem: git-config
tags: [git, config, tdd, pydantic]
dependency_graph:
  requires: []
  provides: [GitConfig, auto_commit_yaml, push_to_remote, pull_from_remote, get_status, get_log]
  affects: [src/bagels/config.py, src/bagels/git/operations.py]
tech_stack:
  added: [threading.Lock for git serialization]
  patterns: [Pydantic BaseModel nested config, TDD red-green]
key_files:
  created:
    - src/bagels/git/operations.py
    - tests/test_git_config.py
    - tests/git/conftest.py
    - tests/git/test_operations.py
  modified:
    - src/bagels/config.py
decisions:
  - "Remove tests/git/__init__.py to avoid shadowing gitpython's 'git' package on sys.path"
  - "Place tmp_git_repo fixture in tests/git/conftest.py (no __init__.py) so bare 'from git import Repo' resolves to gitpython"
metrics:
  duration: 4min
  completed_date: "2026-03-16"
  tasks_completed: 2
  files_modified: 5
requirements_met: [CFG-01, CFG-02, CFG-03, CFG-04, CFG-05, GIT-02, GIT-07]
---

# Phase 3 Plan 01: GitConfig Model and Git Operations Module Summary

**One-liner:** GitConfig Pydantic model with 7-field defaults + thread-safe git operations module (auto_commit_yaml, push/pull, status, log) gating all Phase 3 automation.

## What Was Built

### GitConfig model (src/bagels/config.py)
Added `GitConfig(BaseModel)` following the existing nested model pattern (`Defaults`, `Hotkeys`, etc.) with fields:
- `enabled: bool = False`
- `auto_commit: bool = True`
- `auto_push: bool = False`
- `auto_pull: bool = False`
- `remote: str = "origin"`
- `branch: str = "main"`
- `commit_message_format: str | None = None`

Added `git: GitConfig = GitConfig()` to `Config` model — persisted automatically via `ensure_yaml_fields`.

### Git operations module (src/bagels/git/operations.py)
- `_GIT_LOCK = threading.Lock()` — serializes all index-write operations
- `_get_repo() -> Repo | None` — opens repo at `data_directory()`, returns None on invalid repo
- `auto_commit_yaml(filepath, message) -> bool` — acquires lock, stages file, checks dirty, commits; returns False (never raises) when no repo
- `push_to_remote(remote_name, branch) -> bool` — pushes to remote under lock
- `pull_from_remote(remote_name, branch, silent) -> bool` — pulls from remote under lock
- `get_status() -> list[str]` — returns changed + untracked file paths (no lock, read-only)
- `get_log(max_count) -> list[dict]` — returns `{hash, message, date, author}` dicts; empty list when no repo

### Tests
- `tests/test_git_config.py` — 6 tests covering CFG-01..CFG-05 (GitConfig defaults, Config.git field, custom values, commit_message_format, YAML persistence)
- `tests/git/conftest.py` — `tmp_git_repo` fixture (init repo, configure user, create records/ dir)
- `tests/git/test_operations.py` — 8 tests covering GIT-02, GIT-07 (auto_commit_yaml x3, get_status x2, get_log x2, _GIT_LOCK x1)

**Final result:** 14/14 tests passing.

## Commits

| Hash | Message |
|------|---------|
| 9ae6e9f | test(03-01): add failing tests for GitConfig model and git operations |
| b5abf32 | feat(03-01): implement GitConfig model and git operations module |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed tests/git/__init__.py to fix gitpython import shadow**
- **Found during:** Task 2 (GREEN phase) — running tests
- **Issue:** `tests/git/__init__.py` caused `tests/git/` to be treated as the `git` package when pytest added `tests/` to `sys.path`. Any `from git import Repo` anywhere (including `src/bagels/git/repository.py`) resolved to the empty `tests/git/__init__.py` instead of gitpython.
- **Fix:** Removed `tests/git/__init__.py`. Moved `tmp_git_repo` fixture to `tests/git/conftest.py`. Pytest discovers tests in subdirectories without requiring `__init__.py`.
- **Files modified:** removed `tests/git/__init__.py`, created `tests/git/conftest.py`

## Self-Check

## Self-Check: PASSED

- src/bagels/config.py: FOUND
- src/bagels/git/operations.py: FOUND
- tests/test_git_config.py: FOUND
- tests/git/conftest.py: FOUND
- tests/git/test_operations.py: FOUND
- commit 9ae6e9f: FOUND
- commit b5abf32: FOUND
- 14/14 tests passing
