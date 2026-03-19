---
phase: quick-5
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tests/integration/conftest.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "All 268 tests pass when running uv run pytest"
    - "Tests run in isolation without database conflicts"
    - "Integration tests use unique temp directories per test"
  artifacts:
    - path: "tests/integration/conftest.py"
      provides: "Integration test fixtures with proper isolation"
      contains: "sample_cli_db"
  key_links:
    - from: "tests/integration/conftest.py::sample_cli_db"
      to: "TemporaryDirectory"
      via: "unique temp directory per test"
---

<objective>
Fix test isolation issues causing 90 errors when running `uv run pytest`.

Purpose: Tests should pass reliably when run together, not just individually.
Output: All 268 tests passing with proper database isolation.
</objective>

<execution_context>
@/Users/thepbordin/.claude/get-shit-done/workflows/execute-plan.md
@/Users/thepbordin/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>

## Problem Analysis

Running `uv run pytest` produces 42 failed, 136 passed, 90 errors. The errors are:
```
sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: account.slug
```

**Root cause:** The `sample_cli_db` fixture in `tests/integration/conftest.py` uses a `TemporaryDirectory` with `set_custom_root(tmpdir)`. However:

1. Three conftest.py files (root, cli, integration) all call `set_custom_root(_test_temp_dir)` at module level
2. After `sample_cli_db` yields and calls `set_custom_root(None)`, subsequent tests may inherit the wrong state
3. The fixture doesn't properly isolate the database - tests share the same database file

**Fix:** Use a function-scoped temp directory with unique naming, and ensure the database is created fresh for each test using the fixture.

</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix sample_cli_db fixture isolation</name>
  <files>tests/integration/conftest.py</files>
  <action>
Modify the `sample_cli_db` fixture in `tests/integration/conftest.py` to ensure proper test isolation:

1. Remove the module-level `_test_temp_dir` and `set_custom_root()` calls (lines 16-17)
2. Remove the session-scoped `cleanup_test_temp_dir` fixture (lines 42-49) since each test will manage its own temp dir
3. Keep the config initialization logic but move it into a function that creates config on-demand
4. Update `sample_cli_db` fixture to:
   - Create a unique temp directory per test using `tempfile.mkdtemp()` with a unique prefix
   - Set `set_custom_root(tmpdir)` at the START of the fixture
   - Initialize the database AFTER setting custom root
   - Yield the session
   - Clean up: close session, remove the temp directory explicitly
   - Reset `set_custom_root(None)` only after cleanup

The key change is that each test using `sample_cli_db` gets its OWN temp directory and database, not sharing with other tests.

Also update the `cli_runner` fixture to be a simple function that returns `CliRunner()` without any setup.
  </action>
  <verify>
    <automated>uv run pytest 2>&1 | tail -5</automated>
  </verify>
  <done>
    - All 268 tests pass (or at least 260+ with remaining failures being unrelated to isolation)
    - No UNIQUE constraint errors from database conflicts
    - Running tests multiple times produces consistent results
  </done>
</task>

</tasks>

<verification>
1. Run `uv run pytest` and verify all tests pass
2. Run `uv run pytest tests/integration/` specifically to verify integration tests work
3. Run `uv run pytest tests/cli/` to verify CLI tests work
</verification>

<success_criteria>
- `uv run pytest` shows 0 errors related to UNIQUE constraints
- All 268 tests pass or remaining failures are unrelated to test isolation
</success_criteria>

<output>
After completion, create `.planning/quick/5-run-uv-run-pytest/5-SUMMARY.md`
</output>
