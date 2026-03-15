---
phase: 03-automation
plan: "03"
subsystem: git-cli
tags: [git, cli, click, tdd]
dependency_graph:
  requires: [GitConfig, auto_commit_yaml, push_to_remote, pull_from_remote, get_status, get_log]
  provides: [bagels git status, bagels git log, bagels git sync, bagels git pull]
  affects: [src/bagels/cli/git.py, src/bagels/__main__.py]
tech_stack:
  added: []
  patterns: [Click group with lazy imports, TDD red-green]
key_files:
  created:
    - src/bagels/cli/git.py
    - tests/cli/test_git.py
  modified:
    - src/bagels/__main__.py
decisions:
  - "Lazy imports inside each command body to avoid circular import at module load"
  - "_run_full_import() helper in git.py mirrors the import command sequence for pull reimport step"
  - "pull command uses sys.exit(1) for pull failure to ensure non-zero exit across Click/CliRunner"
metrics:
  duration: 2min
  completed_date: "2026-03-16"
  tasks_completed: 2
  files_modified: 3
requirements_met: [GIT-03, GIT-04, GIT-05, GIT-06]
---

# Phase 3 Plan 03: bagels git CLI Command Group Summary

**One-liner:** Click `git` group with four subcommands (status/log/sync/pull) registered in __main__.py; pull follows safe export→commit→pull→reimport sequence to prevent data loss.

## What Was Built

### src/bagels/cli/git.py

`@click.group(invoke_without_command=True)` named `git` with help text printed when invoked bare.

**`git status`**
- Lazy-imports `get_status` from `bagels.git.operations`
- Empty list → "Working tree clean — no uncommitted changes."
- Non-empty list → each file path + count summary

**`git log`**
- Optional `--count` (default 10) option
- Lazy-imports `get_log`
- Empty list → "No commits found."
- Non-empty → formats each entry as `{hash}  {date}  {message}`

**`git sync`**
- `init_db()` + `load_config()` for config access
- `get_status()` → `auto_commit_yaml(data_dir / path, "sync: {path}")` per dirty file
- `push_to_remote(CONFIG.git.remote, CONFIG.git.branch)` — prints yellow warning if False, exits 0 (non-blocking)
- Prints "Synced N file(s), pushed to remote/branch" on success

**`git pull`** (safe sequence per RESEARCH.md Pitfall 5):
1. `init_db()` + `load_config()`
2. Full export: `export_accounts/categories/persons/templates/records_by_month`
3. `get_status()` → commit any export changes via `auto_commit_yaml`
4. `pull_from_remote(remote, branch)` — prints error to stderr + `sys.exit(1)` on failure
5. `_run_full_import()` — reimports all YAML into SQLite
6. Prints "Pull complete — YAML reimported into database"

**`_run_full_import()` helper** (module-level, patchable in tests):
- Opens fresh Session, imports accounts/categories/persons/templates/records in correct order
- Mirrors the `bagels import` command sequence

### src/bagels/__main__.py

Added:
```python
from bagels.cli.git import git as git_command
cli.add_command(git_command, name="git")
```

### tests/cli/test_git.py

10 tests using `CliRunner(mix_stderr=False)` and `unittest.mock.patch`:
- Tests 1-3: `git status` (dirty / clean / no-repo)
- Tests 4-5: `git log` (with commits / no commits)
- Tests 6-7: `git sync` (commit+push verified by mock counts / push failure exits 0)
- Tests 8-9: `git pull` (call_order verifies export<pull<reimport / failure exits nonzero)
- Test 10: `git` bare invocation shows help with all 4 subcommands

**Final result:** 10/10 tests passing.

## Commits

| Hash | Message |
|------|---------|
| 4663878 | test(03-03): add failing tests for bagels git CLI command group |
| 51809d2 | feat(03-03): implement bagels git CLI command group |

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- src/bagels/cli/git.py: FOUND
- tests/cli/test_git.py: FOUND
- git_command registered in src/bagels/__main__.py: FOUND
- commit 4663878: FOUND
- commit 51809d2: FOUND
- 10/10 tests passing
