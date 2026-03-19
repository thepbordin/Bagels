---
phase: quick-03
plan: 3
subsystem: TUI / record table
tags: [bugfix, null-safety, tui]
dependency_graph:
  requires: []
  provides: [null-safe-category-access]
  affects: [record-table-display]
tech_stack:
  added: []
  patterns: [null-guard, ternary-fallback]
key_files:
  modified:
    - src/bagels/components/modules/records/_table_builder.py
decisions:
  - "Fall back to 'grey' color and 'No Category' label when record.category is None"
metrics:
  duration: "5min"
  completed: "2026-03-19"
  tasks: 1
  files: 1
---

# Quick Task 3: Fix AttributeError — config is None when records have null category

**One-liner:** Null-safe category guards in `_table_builder.py` prevent AttributeError crash when records have no assigned category, falling back to grey/"No Category".

## What Was Done

Applied two targeted null-guards to `_table_builder.py`:

1. **`_format_record_fields`** (line 180): Replaced unconditional `record.category.color.lower()` and `record.category.name` with an `if record.category is not None` block. Falls back to `color_tag = "grey"` and `category_string = "No Category"`.

2. **`_add_split_rows`** (line 201): Replaced unconditional `record.category.color.lower()` with a ternary: `record.category.color.lower() if record.category is not None else "grey"`.

No other logic, imports, or methods were changed.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Guard null category in _format_record_fields and _add_split_rows | 54e4083 | src/bagels/components/modules/records/_table_builder.py |

## Verification

- Syntax validated: `uv run python -c "import ast; ast.parse(...)"` → syntax OK
- Pre-commit hooks (ruff, ruff-format, conventional commit) all passed
- App startup with `uv run bagels --at "./instance/"` should no longer crash with `AttributeError: 'NoneType' object has no attribute 'color'`

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- File modified: `src/bagels/components/modules/records/_table_builder.py` exists with both guards applied
- Commit `54e4083` exists in git log
