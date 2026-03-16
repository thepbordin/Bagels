# Phase 3: Automation - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Automate the YAML export/import lifecycle and Git operations for seamless sync. Every record CRUD operation triggers a targeted YAML export. Application startup auto-imports YAML into SQLite. Git operations (commit, push, pull, status, log) are available via `bagels git` commands with optional automation via config.

</domain>

<decisions>
## Implementation Decisions

### Auto-Export Hook Placement
- **Manager layer** is the hook point — export triggers inside create/update/delete in `src/bagels/managers/` (not the TUI component layer)
- Catches all callers: TUI, CLI, future scripts — no caller needs to remember to export
- Applies to **all entity types**: accounts, categories, persons, templates, and records all trigger export on change
- **Targeted export scope**: when a record is saved, only the affected `YYYY-MM.yaml` month file is re-exported (not all records, not all entities)
- Non-record entities (accounts, categories, persons, templates) export their respective YAML file on change

### Startup Import Behavior
- **Always auto-import on startup**: every startup syncs YAML → SQLite to ensure SQLite reflects the latest Git state
- **TUI loads first, import runs in background**: TUI appears immediately, YAML import runs as background task with a subtle status indicator — best perceived performance
- **Config-controlled auto-pull** (`auto_pull: true`): before startup import, optionally run `git pull` from remote — off by default, user opts in for multi-device sync
- Auto-pull fails gracefully if offline or no remote configured

### Git Command Interface
- `bagels git sync` — commit all uncommitted YAML changes + push to remote
- `bagels git pull` — pull from remote + auto-import updated YAML
- `bagels git status` — show uncommitted YAML changes
- `bagels git log` — show recent Git history
- Auto-commit triggers after every successful YAML export (if `git.auto_commit: true`)
- Auto-push is separate from auto-commit — controlled by `git.auto_push: true` config

### Configuration Keys
- `git.enabled` — master switch for all Git integration (default: false)
- `git.auto_commit` — auto-commit after each YAML export (default: true when git.enabled)
- `git.auto_push` — auto-push after each auto-commit (default: false)
- `git.auto_pull` — auto-pull from remote on startup before import (default: false)
- `git.remote` — remote name (default: "origin")
- `git.branch` — branch name (default: "main")
- `git.commit_message_format` — optional custom format (default: descriptive auto-messages)

### Git Failure Handling
- Git operations are **non-blocking** — CRUD operations succeed even if git fails
- Git errors are logged (not shown in TUI UI unless user runs explicit git command)
- Background failures surface as a subtle warning indicator, not a blocking error

### Claude's Discretion
- Exact debounce/batching strategy if multiple rapid saves happen in sequence
- Background task implementation approach (threading, asyncio, Textual workers)
- Commit message format templates (e.g., "feat(records): add expense 'Coffee' 2026-03-16")
- Git status indicator placement in TUI
- Exact startup progress/status indicator design

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`src/bagels/git/repository.py`** — `initialize_git_repo()` and `create_gitignore()` already implemented; uses `gitpython` library (`from git import Repo`)
- **`src/bagels/managers/records.py`** — `create_record`, `update_record`, `delete_record` are the hook points; `create_record_and_splits` and `update_record_and_splits` are the composite wrappers called by TUI
- **`src/bagels/export/exporter.py`** — existing YAML export functions from Phase 1 to re-use
- **`src/bagels/config.py`** — Pydantic-based config with `BaseModel`; add new `GitConfig` model
- **`src/bagels/locations.py`** — handles data directory paths; extend for git repo path

### Established Patterns
- **Manager pattern** — business logic in `src/bagels/managers/`, each manager has CRUD methods; auto-export hooks added here
- **Pydantic config models** — config sections are nested Pydantic `BaseModel` classes (e.g., `Defaults`, `Hotkeys`); add `GitConfig` the same way
- **gitpython library** — already installed and used in `git/repository.py`; use `Repo` for all git operations

### Integration Points
- **Hook site**: `src/bagels/managers/records.py` (and other managers) — after SQLite write, call export function
- **Startup hook**: `src/bagels/app.py` — add background import worker on startup (Textual has `run_worker` for background tasks)
- **Git commit trigger**: after each successful YAML export, if `git.auto_commit` is enabled, commit the affected file
- **CLI entry**: `src/bagels/__main__.py` — add `bagels git` command group alongside existing CLI commands

</code_context>

<specifics>
## Specific Ideas

- Background startup import: "TUI loads first" — Textual's worker system (`run_worker`) is the natural fit for this
- Manager-layer hooks are clean: any future CLI or scripting usage of managers gets auto-export for free without extra effort
- Targeted month-file export: keeps git diffs small and meaningful — a single record change produces a diff only in that month's file

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-automation*
*Context gathered: 2026-03-16*
