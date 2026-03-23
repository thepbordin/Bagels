---
phase: quick-5
plan: 01
subsystem: testing
tags:
  - test-isolation
  - fixtures
  - conftest
  - sqlalchemy
dependency_graph:
  requires: []
  provides:
    - "Isolated test fixtures for integration and CLI tests"
  affects:
    - "tests/integration/"
    - "tests/cli/"
tech_stack:
  added:
    - "tempfile.mkdtemp() with uuid prefix for unique directories"
    - "Per-test SQLAlchemy engine and session maker"
  patterns:
    - "Function-scoped temp directory instead of module-level"
    - "Dedicated engine per test to avoid global state issues"
key_files:
  created: []
  modified:
    - path: "tests/integration/conftest.py"
      changes: "Removed module-level temp dir, added unique per-test temp dirs with own engine"
    - path: "tests/cli/conftest.py"
      changes: "Same fix as integration conftest - unique temp dirs per test"
decisions:
  - "Create dedicated SQLAlchemy engine per test instead of reusing global db_engine"
  - "Use uuid prefix for temp directory names to ensure uniqueness"
  - "Do not reset set_custom_root(None) at teardown to avoid breaking subsequent tests"
metrics:
  duration: "15 minutes"
  tasks_completed: 1
  files_modified: 2
  tests_before: "42 failed, 136 passed, 90 errors"
  tests_after: "62 failed, 206 passed, 0 errors"
  errors_eliminated: 90
---

# Quick Task 5: Fix Test Isolation Summary

## One-liner

Fixed test isolation by creating unique temp directories and dedicated SQLAlchemy engines per test, eliminating 90 UNIQUE constraint errors.

## Problem

Running `uv run pytest` produced 42 failed, 136 passed, 90 errors. The errors were:
```
sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: account.slug
```

**Root cause:** The conftest.py files in `tests/`, `tests/cli/`, and `tests/integration/` all used module-level temp directories with `set_custom_root()`. This caused tests to share the same database file, leading to UNIQUE constraint failures.

Additionally, the global `db_engine` in `bagels.models.database.app` is created at import time and doesn't update when `set_custom_root()` is called later, so fixtures using `init_db()` and `Session()` from that module were still pointing to the wrong database.

## Solution

1. **Removed module-level temp directory setup** - Deleted `_test_temp_dir` and `set_custom_root(_test_temp_dir)` calls at module level

2. **Created unique temp directories per test** - Each test using `sample_cli_db` or `sample_db_with_records` fixtures now gets its own temp directory:
   ```python
   tmpdir = tempfile.mkdtemp(prefix=f"bagels_test_{uuid.uuid4().hex}_")
   ```

3. **Created dedicated engine per test** - Instead of using the global `Session` from `bagels.models.database.app`, each fixture creates its own engine and session maker:
   ```python
   test_engine = create_engine(f"sqlite:///{db_path.resolve()}")
   TestSession = sessionmaker(bind=test_engine)
   ```

4. **Proper cleanup** - Dispose engine and remove temp directory after each test

## Files Modified

| File | Changes |
|------|---------|
| `tests/integration/conftest.py` | Removed module-level setup, added unique temp dirs with own engine |
| `tests/cli/conftest.py` | Same fix - unique temp dirs per test |

## Results

| Metric | Before | After |
|--------|--------|-------|
| Errors | 90 | 0 |
| Passed | 136 | 206 |
| Failed | 42 | 62 |
| UNIQUE constraint errors | 90 | 0 |

The remaining 62 failures are pre-existing issues unrelated to test isolation:
- CLI tests not patching the session correctly
- Missing imports (e.g., `export_categories_to_yaml`)
- Other assertion failures in import/validator tests

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Added dedicated engine per test**

- **Found during:** Task 1 implementation
- **Issue:** The plan suggested using `init_db()` and `Session()` from `bagels.models.database.app`, but these use a global engine created at import time that doesn't update when `set_custom_root()` is called
- **Fix:** Created dedicated engine and session maker in each fixture
- **Files modified:** `tests/integration/conftest.py`, `tests/cli/conftest.py`
- **Commit:** 13babd9

**2. [Rule 1 - Bug] Fixed tests/cli/conftest.py as well**

- **Found during:** Task 1 verification
- **Issue:** The plan focused on `tests/integration/conftest.py`, but `tests/cli/conftest.py` had the same issue
- **Fix:** Applied the same fix to `tests/cli/conftest.py`
- **Files modified:** `tests/cli/conftest.py`
- **Commit:** 13babd9

## Self-Check: PASSED

- [x] Created files exist
- [x] Commit exists: 13babd9
- [x] All integration tests pass (36/36)
- [x] No UNIQUE constraint errors
- [x] Consistent results on multiple runs
