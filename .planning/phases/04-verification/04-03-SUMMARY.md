---
phase: "04-verification"
plan: "03"
subsystem: "importer"
tags: [conflict-detection, git, import, safety, integration-tests]
dependency_graph:
  requires: []
  provides: [ConflictError, check_for_conflict_markers]
  affects: [run_full_import, bagels-git-pull]
tech_stack:
  added: []
  patterns: [fail-fast-before-import, pre-import-scan]
key_files:
  created:
    - tests/integration/test_git_conflict.py
  modified:
    - src/bagels/importer/importer.py
decisions:
  - "Conflict check runs as the FIRST operation in run_full_import() before any YAML is loaded or DB touched"
  - "ConflictError carries a list of conflicting file paths for precise user feedback"
  - "check_for_conflict_markers() scans: accounts/categories/persons/templates.yaml + all records/*.yaml"
metrics:
  duration: "3 minutes"
  completed: "2026-03-19"
  tasks: 2
  files: 2
---

# Phase 4 Plan 03: Git Conflict Detection Summary

**One-liner:** ConflictError + check_for_conflict_markers() fail-fast guard in run_full_import() with 6 passing integration tests including two-clone git simulation.

## What Was Built

Added safety guardrails to `run_full_import()` so it atomically rejects imports when any YAML file contains unresolved git conflict markers (`<<<<<<< HEAD`). This prevents silent import of corrupt/conflicted data.

### Task 1: Add conflict marker detection to run_full_import()

Modified `src/bagels/importer/importer.py`:

- Added `CONFLICT_MARKER = "<<<<<<< HEAD"` constant
- Added `ConflictError(Exception)` class with `conflicting_files: list[str]` attribute and informative message naming all conflicting files
- Added `check_for_conflict_markers(data_dir: Path) -> list[str]` helper that scans accounts/categories/persons/templates.yaml and all records/*.yaml
- Modified `run_full_import()` to call `check_for_conflict_markers()` as the very first operation — before opening any files or touching the DB

### Task 2: Write git conflict integration tests

Created `tests/integration/test_git_conflict.py` with 6 tests:

**TestConflictMarkerDetection (5 tests):**
- `test_import_rejected_when_conflict_markers_in_yaml` — ConflictError raised, message contains filename
- `test_import_rejected_when_conflict_in_records_file` — works for records subdirectory files
- `test_import_succeeds_after_conflict_resolution` — clean YAML imports correctly, account found in DB
- `test_check_for_conflict_markers_returns_files` — helper returns relative path list
- `test_check_for_conflict_markers_clean_returns_empty` — returns [] for clean files

**TestTwoCloneConflictSimulation (1 test):**
- `test_two_clone_diverge_and_conflict` — simulates real two-device git workflow using gitpython: bare origin → clone A pushes → clone B diverges + pulls → conflict markers detected

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected data directory path in tests**
- **Found during:** Task 2 (test execution)
- **Issue:** Plan spec wrote YAML to `tmp_path / "data" / "accounts.yaml"`, but `set_custom_root(tmp_path)` causes `data_directory()` to return `tmp_path` directly (not a "data" subdirectory)
- **Fix:** Changed all test file writes to `tmp_path / "accounts.yaml"` and `tmp_path / "records"` to match actual `data_directory()` behavior
- **Files modified:** tests/integration/test_git_conflict.py
- **Commit:** 8f83aea

## Success Criteria Verification

- [x] `src/bagels/importer/importer.py` has `ConflictError` class and `check_for_conflict_markers()` function
- [x] `run_full_import()` raises `ConflictError` before any data is imported when conflict markers present
- [x] Error message includes the filename with conflicts
- [x] `tests/integration/test_git_conflict.py` has 6 tests, all passing
- [x] Post-resolution import succeeds and data is correct in SQLite
- [x] Existing import tests unaffected (pre-existing failures confirmed pre-existed before this plan)

## Self-Check: PASSED

All key files exist and both task commits are present in git history.
