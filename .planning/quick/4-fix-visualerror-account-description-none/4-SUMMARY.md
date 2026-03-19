---
phase: quick-4
plan: 1
subsystem: TUI / AccountMode
tags: [bug-fix, null-guard, textual, account]
dependency_graph:
  requires: []
  provides: [stable AccountMode.rebuild() for None descriptions]
  affects: [src/bagels/components/modules/accountmode.py]
tech_stack:
  added: []
  patterns: [null-guard via `or ""`]
key_files:
  created: []
  modified:
    - src/bagels/components/modules/accountmode.py
decisions:
  - "Use `or \"\"` (not str()) to match the existing pattern on line 32"
metrics:
  duration: "2min"
  completed_date: "2026-03-19T08:59:59Z"
  tasks_completed: 1
  files_modified: 1
---

# Quick Task 4: Fix VisualError — account.description None in rebuild() Summary

## One-liner

Null-guarded `description_label.update()` in `AccountMode.rebuild()` with `account.description or ""` to prevent Textual VisualError when account has no description.

## What Was Done

### Task 1: Guard account.description in description_label.update()

Applied a one-line fix at line 107 of `src/bagels/components/modules/accountmode.py`.

**Before:**
```python
description_label.update(account.description)
```

**After:**
```python
description_label.update(account.description or "")
```

Textual's `Label.update()` requires a `str` or Rich renderable — passing `None` raises a `VisualError`. The fix mirrors the identical null-guard already present on line 32 inside `AccountsList.__init__`.

**Commit:** `7075e7b`

## Deviations from Plan

None - plan executed exactly as written.

## Verification

- `description_label.update(account.description or "")` is present at the fix site.
- File parses cleanly (AST parse confirmed, no SyntaxError).
- Pre-commit hooks (ruff lint + format, conventional commit) all passed.

## Self-Check: PASSED

- File modified: `src/bagels/components/modules/accountmode.py` — FOUND
- Commit `7075e7b` — FOUND
