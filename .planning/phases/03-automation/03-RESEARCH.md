# Phase 3: Automation - Research

**Researched:** 2026-03-16
**Domain:** Python hook patterns, gitpython operations, Textual workers, Pydantic config extension
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Auto-Export Hook Placement**
- Manager layer is the hook point — export triggers inside create/update/delete in `src/bagels/managers/` (not the TUI component layer)
- Catches all callers: TUI, CLI, future scripts — no caller needs to remember to export
- Applies to all entity types: accounts, categories, persons, templates, and records all trigger export on change
- Targeted export scope: when a record is saved, only the affected `YYYY-MM.yaml` month file is re-exported (not all records, not all entities)
- Non-record entities (accounts, categories, persons, templates) export their respective YAML file on change

**Startup Import Behavior**
- Always auto-import on startup: every startup syncs YAML → SQLite to ensure SQLite reflects the latest Git state
- TUI loads first, import runs in background: TUI appears immediately, YAML import runs as background task with a subtle status indicator — best perceived performance
- Config-controlled auto-pull (`auto_pull: true`): before startup import, optionally run `git pull` from remote — off by default, user opts in for multi-device sync
- Auto-pull fails gracefully if offline or no remote configured

**Git Command Interface**
- `bagels git sync` — commit all uncommitted YAML changes + push to remote
- `bagels git pull` — pull from remote + auto-import updated YAML
- `bagels git status` — show uncommitted YAML changes
- `bagels git log` — show recent Git history
- Auto-commit triggers after every successful YAML export (if `git.auto_commit: true`)
- Auto-push is separate from auto-commit — controlled by `git.auto_push: true` config

**Configuration Keys**
- `git.enabled` — master switch for all Git integration (default: false)
- `git.auto_commit` — auto-commit after each YAML export (default: true when git.enabled)
- `git.auto_push` — auto-push after each auto-commit (default: false)
- `git.auto_pull` — auto-pull from remote on startup before import (default: false)
- `git.remote` — remote name (default: "origin")
- `git.branch` — branch name (default: "main")
- `git.commit_message_format` — optional custom format (default: descriptive auto-messages)

**Git Failure Handling**
- Git operations are non-blocking — CRUD operations succeed even if git fails
- Git errors are logged (not shown in TUI UI unless user runs explicit git command)
- Background failures surface as a subtle warning indicator, not a blocking error

### Claude's Discretion
- Exact debounce/batching strategy if multiple rapid saves happen in sequence
- Background task implementation approach (threading, asyncio, Textual workers)
- Commit message format templates (e.g., "feat(records): add expense 'Coffee' 2026-03-16")
- Git status indicator placement in TUI
- Exact startup progress/status indicator design

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-07 | Auto-export YAML on every record save/update/delete | Manager hook pattern + targeted month-file export function |
| DATA-08 | Auto-import YAML on application startup | Textual `run_worker` / `@work` decorator in `app.py` `on_mount` |
| GIT-02 | Auto-commit YAML changes with descriptive messages | gitpython `Repo.index.add()` + `index.commit()` pattern |
| GIT-03 | `bagels git sync` command (commit + push) | Click command group added to `__main__.py` |
| GIT-04 | `bagels git pull` command (pull + reimport) | gitpython `remote.pull()` + existing importer |
| GIT-05 | `bagels git status` command (show uncommitted changes) | gitpython `repo.is_dirty()` + `repo.untracked_files` |
| GIT-06 | `bagels git log` command (show recent history) | gitpython `repo.iter_commits()` |
| GIT-07 | Optional auto-push to remote (configurable) | `git.auto_push` config key + gitpython `remote.push()` |
| GIT-08 | Pull remote changes on startup and import YAML | `git.auto_pull` config key + Textual worker pre-import pull |
| CFG-01 | Add `git.enabled` config option | Nested Pydantic `GitConfig` model added to `Config` |
| CFG-02 | Add `git.auto_commit` config option | Field in `GitConfig` model |
| CFG-03 | Add `git.auto_push` config option | Field in `GitConfig` model |
| CFG-04 | Add `git.remote` and `git.branch` config options | Fields in `GitConfig` model |
| CFG-05 | Add `git.commit_message_format` config option | Optional str field in `GitConfig` model |
</phase_requirements>

---

## Summary

Phase 3 automates the YAML export/import lifecycle and adds Git sync operations. All the infrastructure already exists: gitpython is installed, `initialize_git_repo()` is implemented, the exporter has all entity functions, and the importer is complete. The phase is primarily about wiring hooks into existing code — not building new capabilities from scratch.

The three main integration areas are: (1) post-write hooks in each manager module that call the relevant exporter and optionally auto-commit via gitpython; (2) a Textual background worker in `app.py`'s `on_mount` that runs the startup import (and optional auto-pull); and (3) a `bagels git` Click command group with `sync`, `pull`, `status`, and `log` subcommands wired into `__main__.py`.

The only genuine new code is `src/bagels/git/operations.py` (commit, push, pull, status, log helpers), the `GitConfig` Pydantic model added to `src/bagels/config.py`, and a targeted single-month export helper in `src/bagels/export/exporter.py` to keep git diffs small.

**Primary recommendation:** Use the `@work` decorator (thread mode) in Textual for startup import, gitpython `Repo` for all git operations — both are already in the dependency tree and no new packages are needed.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| gitpython | >=3.1,<4.0 | All git operations (commit, push, pull, status, log) | Already installed, `Repo` already used in `src/bagels/git/repository.py` |
| textual | >=1.0,<2.0 | `@work` decorator for background startup import | Already the TUI framework; worker system is built-in |
| pydantic | >=2.0,<3.0 | `GitConfig` nested model for config | Already used for all config models |
| click | >=8.0,<9.0 | `bagels git` command group | Already the CLI framework |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| threading (stdlib) | N/A | Background git ops outside Textual context | For auto-commit triggered from manager layer, which is not inside TUI app lifecycle |
| logging (stdlib) | N/A | Non-blocking error logging for git failures | Log-only pattern — no user-visible error for background git failures |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| gitpython | subprocess `git` calls | gitpython gives structured return objects and exceptions; subprocess is fragile with path/env issues |
| `@work` decorator | `asyncio.create_task` | Textual's worker system integrates with the app lifecycle and provides `worker_state_changed` events; `asyncio` requires care to not block the TUI event loop |
| threading for manager hooks | asyncio | Manager CRUD methods are synchronous; threading is the natural fit without refactoring everything to async |

**Installation:** No new packages needed — all dependencies are already declared in `pyproject.toml`.

---

## Architecture Patterns

### Recommended Project Structure
```
src/bagels/
├── git/
│   ├── repository.py       # existing: init, gitignore
│   └── operations.py       # NEW: commit, push, pull, status, log helpers
├── managers/
│   ├── records.py          # ADD hooks: after create/update/delete, call export + git
│   ├── accounts.py         # ADD hooks
│   ├── categories.py       # ADD hooks
│   ├── persons.py          # ADD hooks
│   └── record_templates.py # ADD hooks
├── export/
│   └── exporter.py         # ADD: export_records_for_month(session, output_dir, year, month)
├── cli/
│   └── git.py              # NEW: bagels git command group (sync, pull, status, log)
├── config.py               # ADD: GitConfig model, git field on Config
└── app.py                  # ADD: run_worker for startup import in on_mount
```

### Pattern 1: Manager Hook — Post-Write Export + Auto-Commit

**What:** After a successful SQLite write, call the relevant exporter, then (if `git.auto_commit` enabled) trigger a git commit in a background thread.

**When to use:** Every create/update/delete in every manager. The hook must not raise — wrap in try/except and log errors silently.

**Example:**
```python
# In src/bagels/managers/records.py
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

def _trigger_export_and_commit(record_date: datetime, operation: str, label: str) -> None:
    """Run export and optional git commit in background thread."""
    try:
        from bagels.config import CONFIG
        from bagels.models.database.app import Session
        from bagels.export.exporter import export_records_for_month
        from bagels.locations import data_directory

        session = Session()
        try:
            year, month = record_date.year, record_date.month
            export_records_for_month(session, data_directory(), year, month)
        finally:
            session.close()

        if CONFIG.git.enabled and CONFIG.git.auto_commit:
            from bagels.git.operations import auto_commit_yaml
            month_key = record_date.strftime("%Y-%m")
            msg = f"records({month_key}): {operation} '{label}'"
            auto_commit_yaml(
                filepath=data_directory() / "records" / f"{month_key}.yaml",
                message=msg,
            )
    except Exception:
        logger.exception("Background export/commit failed — CRUD operation unaffected")


def create_record(record_data: dict):
    session = Session()
    try:
        record = Record(**record_data)
        session.add(record)
        session.commit()
        session.refresh(record)
        session.expunge(record)
        # Trigger export in background — non-blocking
        t = threading.Thread(
            target=_trigger_export_and_commit,
            args=(record.date, "add", record.label),
            daemon=True,
        )
        t.start()
        return record
    finally:
        session.close()
```

### Pattern 2: GitConfig Pydantic Model

**What:** Nested `BaseModel` added to `Config`, following exact pattern used by `Defaults`, `Hotkeys`, etc.

**When to use:** Adding `git.*` config keys.

**Example:**
```python
# In src/bagels/config.py
class GitConfig(BaseModel):
    enabled: bool = False
    auto_commit: bool = True
    auto_push: bool = False
    auto_pull: bool = False
    remote: str = "origin"
    branch: str = "main"
    commit_message_format: str | None = None


class Config(BaseModel):
    hotkeys: Hotkeys = Hotkeys()
    symbols: Symbols = Symbols()
    defaults: Defaults = Defaults()
    state: State = State()
    git: GitConfig = GitConfig()  # NEW
```

Note: `ensure_yaml_fields` in `Config` already handles writing new fields to disk via `update_config` — no extra work needed to persist GitConfig defaults.

### Pattern 3: Textual Worker for Startup Import

**What:** Use the `@work` decorator in `app.py`'s `on_mount` to run the full YAML → SQLite import in a background thread. TUI renders immediately; import runs in background.

**When to use:** `on_mount` in `App` class. The `@work` decorator with `thread=True` runs the function in a thread pool managed by Textual.

**Example:**
```python
# In src/bagels/app.py
from textual.worker import get_current_worker
from textual import work

class App(TextualApp):

    def on_mount(self) -> None:
        # ... existing mount code ...
        self.run_startup_import()

    @work(thread=True, exclusive=True)
    def run_startup_import(self) -> None:
        worker = get_current_worker()
        try:
            from bagels.config import CONFIG
            # Optional auto-pull before import
            if CONFIG.git.enabled and CONFIG.git.auto_pull:
                from bagels.git.operations import pull_from_remote
                pull_from_remote(silent=True)  # fails gracefully

            from bagels.importer.importer import run_full_import
            run_full_import()
        except Exception:
            pass  # Never crash TUI on startup import failure
```

Textual's `@work(thread=True)` is the documented pattern for CPU/IO-bound background tasks that must not block the async event loop. The `exclusive=True` flag prevents duplicate workers.

### Pattern 4: gitpython Operations

**What:** `src/bagels/git/operations.py` centralizes all repo-level git actions.

**Example:**
```python
# In src/bagels/git/operations.py
from pathlib import Path
from git import Repo, InvalidGitRepositoryError, GitCommandError
from bagels.locations import data_directory


def _get_repo() -> Repo | None:
    try:
        return Repo(data_directory())
    except InvalidGitRepositoryError:
        return None


def auto_commit_yaml(filepath: Path, message: str) -> bool:
    repo = _get_repo()
    if repo is None:
        return False
    try:
        repo.index.add([str(filepath.relative_to(data_directory()))])
        if repo.is_dirty(index=True):
            repo.index.commit(message)
        return True
    except GitCommandError:
        return False


def push_to_remote(remote_name: str = "origin", branch: str = "main") -> bool:
    repo = _get_repo()
    if repo is None:
        return False
    try:
        remote = repo.remote(remote_name)
        remote.push(branch)
        return True
    except (GitCommandError, ValueError):
        return False


def pull_from_remote(
    remote_name: str = "origin", branch: str = "main", silent: bool = False
) -> bool:
    repo = _get_repo()
    if repo is None:
        return False
    try:
        remote = repo.remote(remote_name)
        remote.pull(branch)
        return True
    except (GitCommandError, ValueError):
        if not silent:
            raise
        return False


def get_status() -> list[str]:
    repo = _get_repo()
    if repo is None:
        return []
    changed = [item.a_path for item in repo.index.diff(None)]
    untracked = list(repo.untracked_files)
    return changed + untracked


def get_log(max_count: int = 10) -> list[dict]:
    repo = _get_repo()
    if repo is None:
        return []
    return [
        {
            "hash": c.hexsha[:7],
            "message": c.message.strip(),
            "date": c.authored_datetime.isoformat(),
            "author": str(c.author),
        }
        for c in repo.iter_commits(max_count=max_count)
    ]
```

### Pattern 5: Click `git` Command Group

**What:** New `bagels/cli/git.py` with a `git` Click group and four subcommands. Registered in `__main__.py` alongside existing commands.

**Example:**
```python
# In src/bagels/cli/git.py
import click

@click.group()
def git():
    """Git sync operations for YAML data."""
    pass

@git.command()
def sync():
    """Commit all YAML changes and push to remote."""
    from bagels.models.database.app import init_db
    from bagels.git.operations import auto_commit_yaml, push_to_remote
    from bagels.config import CONFIG
    init_db()
    # commit all dirty YAML files
    # then push if enabled or always (sync is explicit)
    ...

@git.command()
def pull():
    """Pull from remote and reimport YAML."""
    ...

@git.command()
def status():
    """Show uncommitted YAML changes."""
    ...

@git.command()
def log():
    """Show recent Git history."""
    ...
```

In `__main__.py`:
```python
from bagels.cli.git import git as git_command
cli.add_command(git_command, name="git")
```

### Pattern 6: Targeted Month-File Export

**What:** New helper `export_records_for_month(session, output_dir, year, month)` in `exporter.py`. Filters records to a single month and writes only that `YYYY-MM.yaml` file.

**When to use:** Called from the records manager hook — keeps git diffs to exactly the affected month file.

**Example:**
```python
def export_records_for_month(
    session: Session, output_dir: Path, year: int, month: int
) -> Path:
    """Export only records for the given year/month to records/YYYY-MM.yaml."""
    from datetime import date
    start = date(year, month, 1)
    # end = first day of next month
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    records = (
        session.query(Record)
        .filter(Record.date >= start, Record.date < end)
        .all()
    )
    records_dir = output_dir / "records"
    records_dir.mkdir(exist_ok=True, parents=True)
    month_key = f"{year:04d}-{month:02d}"
    filepath = records_dir / f"{month_key}.yaml"
    # ... same dict-building logic as export_records_by_month ...
    return filepath
```

### Anti-Patterns to Avoid

- **Blocking the TUI event loop with git I/O**: git operations (especially push/pull) can take seconds over slow networks. Always use `threading.Thread(daemon=True)` for auto-commit from manager hooks. In Textual context, use `@work(thread=True)`.
- **Raising exceptions from hooks**: Manager hooks must catch all exceptions. A git failure must never cause a CRUD operation to roll back or the user to see an error dialog.
- **Running full export on every save**: Export only the affected month file for records, or the affected entity file for non-record types. Full re-export on every keystroke would produce noisy git diffs.
- **Importing git at module load time in managers**: Lazy-import `from bagels.git.operations import ...` inside the hook function to avoid circular imports and keep startup fast when git is disabled.
- **Auto-commit when no YAML changes exist**: Always check `repo.is_dirty(index=True)` before calling `index.commit()` to avoid empty commits.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Git operations | Custom subprocess `git` shell calls | `gitpython` `Repo` | Already installed; handles paths, encodings, errors as Python exceptions |
| Background tasks in Textual | `asyncio.create_task` with blocking I/O | `@work(thread=True)` | Textual workers integrate with app lifecycle, handle exceptions safely, support cancellation |
| Config persistence | Manual YAML write-back code | Existing `ensure_yaml_fields()` in `Config` | Already handles merging new fields into existing config YAML |
| Import-on-startup logic | Custom importer code | `bagels.importer.importer` functions | Full importer with validation already exists from Phase 1 |

**Key insight:** Phase 3 is almost entirely wiring — connecting existing pieces. The risk is accidentally over-building rather than under-building.

---

## Common Pitfalls

### Pitfall 1: Git Lock File Contention
**What goes wrong:** When auto-commit fires in a background thread at the same time as the startup import worker (which may do an auto-pull), gitpython raises `GitCommandError: index.lock exists`.
**Why it happens:** Git uses a file lock (`index.lock`) for all index-mutating operations. Two concurrent operations on the same repo will conflict.
**How to avoid:** Use a module-level `threading.Lock()` in `operations.py` that all git write operations acquire before touching the repo. Read-only operations (`status`, `log`) do not need the lock.
**Warning signs:** `GitCommandError` with "index.lock" in the message appearing in logs.

### Pitfall 2: Textual Worker Not Finding DB Session
**What goes wrong:** The startup import worker tries to create a SQLAlchemy session before `init_db()` has been called, because `app.py` `on_mount` runs after the app has started but `init_db()` happens in `__main__.py`.
**Why it happens:** `on_mount` in the `App` class runs after the TUI event loop starts — `init_db()` is called in `__main__.py` before `app.run()`, so this is safe. But if the worker is scheduled too early (e.g., in `__init__`) it can race.
**How to avoid:** Schedule the worker in `on_mount`, not `__init__`. `on_mount` runs after the event loop is established and `__main__.py` has already called `init_db()`.
**Warning signs:** `OperationalError: no such table` inside the worker.

### Pitfall 3: Config Not Loaded When Manager Hooks Fire
**What goes wrong:** `CONFIG` is a module-level global initialized to `None` in `config.py`. If a manager is imported before `load_config()` is called (e.g., in tests), accessing `CONFIG.git.enabled` raises `AttributeError`.
**Why it happens:** Tests and CLI paths sometimes import managers directly without going through `__main__.py`'s startup sequence.
**How to avoid:** In the hook function, guard with `if CONFIG is None or not CONFIG.git.enabled: return` before any git operations. This is already the pattern the config module supports.
**Warning signs:** `AttributeError: 'NoneType' object has no attribute 'git'` in tests.

### Pitfall 4: `ensure_yaml_fields` Writes GitConfig Defaults on Every Startup
**What goes wrong:** `ensure_yaml_fields` in `Config.__init__` writes back all default values to the config YAML. If `git.enabled = False` is the default, it gets written to every user's config file on first launch after upgrade, which is noisy.
**Why it happens:** This is by design in the existing `ensure_yaml_fields` implementation — it adds missing keys with defaults.
**How to avoid:** This is acceptable behavior — it's how all other config sections work (e.g., `hotkeys`, `symbols`). No special handling needed. Just ensure `git.enabled` defaults to `False` so users don't get accidental git integration.
**Warning signs:** Users reporting unexpected new `git:` section appearing in their config file — this is expected, not a bug.

### Pitfall 5: `bagels git pull` Clobbers Local SQLite Changes
**What goes wrong:** User edits data via TUI (writes to SQLite), then runs `bagels git pull` which re-imports YAML into SQLite. If the YAML was not auto-exported yet (e.g., git was just enabled), the reimport overwrites SQLite with stale data.
**Why it happens:** The import is designed to be idempotent but uses YAML as source-of-truth. If SQLite has newer data than YAML, the pull+reimport will lose it.
**How to avoid:** `bagels git pull` must first run a full export (YAML ← SQLite), then commit those changes, then pull from remote (handling merge conflicts), then reimport. Document this clearly. The command should be: export → commit → pull → reimport.
**Warning signs:** User reports "my recent entries disappeared after `bagels git pull`".

### Pitfall 6: `delete_record` Needs Export After Delete
**What goes wrong:** After deleting a record, the manager hook exports the affected month's YAML. But if the deletion makes the month file empty (last record of that month deleted), the file should be removed from the data directory (or written with an empty records dict). If it's left with old content, the importer will reimport the deleted record.
**Why it happens:** The export function overwrites the file with current state — so if the query returns zero records for that month, the file should be written as `{records: {}}` or removed. The existing `export_records_for_month` will handle this correctly if it always writes (even empty).
**How to avoid:** Ensure `export_records_for_month` always writes the file even when zero records exist for that month, so stale data is not left on disk.
**Warning signs:** Deleted records reappearing after restart (startup reimport).

---

## Code Examples

Verified patterns from existing codebase:

### Pydantic nested model pattern (from `config.py`)
```python
class Defaults(BaseModel):
    period: Literal["day", "week", "month", "year"] = "week"
    first_day_of_week: int = Field(ge=0, le=6, default=6)

class Config(BaseModel):
    hotkeys: Hotkeys = Hotkeys()
    defaults: Defaults = Defaults()
    # Add new nested section exactly like this:
    git: GitConfig = GitConfig()
```

### gitpython Repo access (from `src/bagels/git/repository.py`)
```python
from git import Repo, InvalidGitRepositoryError
from pathlib import Path

try:
    repo = Repo(data_dir)     # opens existing repo
except InvalidGitRepositoryError:
    Repo.init(data_dir)       # initializes new repo
```

### gitpython index add + commit
```python
# Source: gitpython docs / existing repository.py pattern
repo.index.add(["records/2026-03.yaml"])
if repo.is_dirty(index=True):
    repo.index.commit("records(2026-03): add expense 'Coffee'")
```

### gitpython remote push/pull
```python
remote = repo.remote("origin")
remote.push("main")          # push
remote.pull("main")          # pull
```

### gitpython status + log
```python
# Changed tracked files
changed = [item.a_path for item in repo.index.diff(None)]
# Untracked files
untracked = repo.untracked_files

# Commit log
for commit in repo.iter_commits(max_count=10):
    print(commit.hexsha[:7], commit.message.strip())
```

### Textual worker pattern (Textual 1.x)
```python
from textual import work
from textual.worker import get_current_worker

class App(TextualApp):
    def on_mount(self) -> None:
        self.run_startup_import()   # call the worker

    @work(thread=True, exclusive=True)
    def run_startup_import(self) -> None:
        # Runs in a thread — does not block TUI event loop
        # Access self.app safely but don't call Textual methods
        # that mutate widgets here — use self.call_from_thread() for that
        try:
            from bagels.importer.importer import run_full_import
            run_full_import()
            self.app.call_from_thread(self._on_import_complete)
        except Exception:
            pass

    def _on_import_complete(self) -> None:
        self.notify("Data synced from YAML", timeout=2)
```

### Manager hook — fire-and-forget thread
```python
import threading
import logging

logger = logging.getLogger(__name__)

def _background_export(record_date, operation, label):
    try:
        # lazy import to avoid circular deps
        from bagels.config import CONFIG
        if CONFIG is None or not CONFIG.git.enabled:
            return
        # ... export + commit ...
    except Exception:
        logger.exception("Background export failed")

# In create_record, after session.expunge(record):
threading.Thread(
    target=_background_export,
    args=(record.date, "add", record.label),
    daemon=True,
).start()
```

### Click command group pattern (from `__main__.py`)
```python
# src/bagels/cli/git.py
import click

@click.group()
def git():
    """Git sync operations."""
    pass

@git.command()
def sync():
    """Commit uncommitted YAML changes and push."""
    pass

# __main__.py
from bagels.cli.git import git as git_command
cli.add_command(git_command, name="git")
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `run_worker()` method call | `@work` decorator | Textual 0.x → 1.x | Cleaner syntax, explicit thread vs async mode |
| `repo.git.add()` subprocess wrapper | `repo.index.add()` | gitpython 3.x | More Pythonic, no shell quoting issues |

**Deprecated/outdated:**
- `repo.git.add(...)` / `repo.git.commit(...)` style: while still functional in gitpython 3.x, prefer `repo.index.add()` / `repo.index.commit()` for structured access without shell escaping.
- `self.run_worker(callable)` in Textual 0.x: replaced by `@work` decorator in Textual 1.x — use `@work(thread=True)`.

---

## Open Questions

1. **Debounce strategy for rapid successive saves**
   - What we know: Multiple rapid CRUD operations (e.g., creating 10 records in a script) will spawn 10 background threads, each exporting and committing the same month file.
   - What's unclear: Whether 10 near-simultaneous commits on the same file is actually a problem in practice.
   - Recommendation: Use the module-level `threading.Lock()` approach — each commit waits for the previous to finish. This naturally serializes operations. If batching is desired, a deque + timer debounce can be added later. For Phase 3, the lock-based serial approach is sufficient and simple.

2. **TUI status indicator design**
   - What we know: `app.notify()` shows a temporary toast notification. The `Footer` widget is already present.
   - What's unclear: Whether a persistent status label ("Syncing...") or a transient `notify()` toast is preferred.
   - Recommendation: Use `self.notify()` for completion ("Import complete") and a subtle footer label for in-progress state. Exact design is Claude's discretion.

3. **`bagels git pull` export-before-pull sequence**
   - What we know: Pull must not clobber uncommitted SQLite-only data.
   - What's unclear: Whether users will always have auto-export enabled when they first run `bagels git pull`.
   - Recommendation: `bagels git pull` should always run a full export + commit of current state before pulling. This is the safest default and avoids data loss.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 8.3.1 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/git/ tests/automation/ -x -q` |
| Full suite command | `uv run pytest tests/ -x -q --ignore=tests/managers/test_utils.py` |

Note: `tests/managers/test_utils.py` fails to collect due to missing `freezegun` — ignore until resolved.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-07 | Auto-export triggers on record create/update/delete | unit | `uv run pytest tests/automation/test_hooks.py -x -q` | Wave 0 |
| DATA-07 | Targeted month-file export only | unit | `uv run pytest tests/export/test_records.py -x -q` | Partial (exists, extend) |
| DATA-08 | Startup import runs on app mount | unit | `uv run pytest tests/automation/test_startup.py -x -q` | Wave 0 |
| GIT-02 | Auto-commit after export when git.auto_commit=True | unit | `uv run pytest tests/git/test_operations.py::test_auto_commit -x -q` | Wave 0 |
| GIT-03 | `bagels git sync` commits + pushes | integration | `uv run pytest tests/cli/test_git.py::test_sync -x -q` | Wave 0 |
| GIT-04 | `bagels git pull` pulls + reimports | integration | `uv run pytest tests/cli/test_git.py::test_pull -x -q` | Wave 0 |
| GIT-05 | `bagels git status` shows uncommitted files | integration | `uv run pytest tests/cli/test_git.py::test_status -x -q` | Wave 0 |
| GIT-06 | `bagels git log` shows commit history | integration | `uv run pytest tests/cli/test_git.py::test_log -x -q` | Wave 0 |
| GIT-07 | auto_push config triggers push after auto-commit | unit | `uv run pytest tests/git/test_operations.py::test_auto_push -x -q` | Wave 0 |
| GIT-08 | auto_pull config triggers pull before startup import | unit | `uv run pytest tests/automation/test_startup.py::test_auto_pull -x -q` | Wave 0 |
| CFG-01..05 | GitConfig model validates and persists correctly | unit | `uv run pytest tests/test_git_config.py -x -q` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/git/ tests/automation/ -x -q 2>/dev/null`
- **Per wave merge:** `uv run pytest tests/ -x -q --ignore=tests/managers/test_utils.py`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/git/__init__.py` — package init
- [ ] `tests/git/test_operations.py` — covers GIT-02, GIT-07; use tmp git repo fixture
- [ ] `tests/automation/__init__.py` — package init
- [ ] `tests/automation/test_hooks.py` — covers DATA-07; mock export/commit functions
- [ ] `tests/automation/test_startup.py` — covers DATA-08, GIT-08; mock importer + pull
- [ ] `tests/cli/test_git.py` — covers GIT-03, GIT-04, GIT-05, GIT-06; use Click test runner + tmp git repo
- [ ] `tests/test_git_config.py` — covers CFG-01 through CFG-05

Existing test infra covers: `in_memory_db`, `temp_directory`, `sample_records` fixtures in `tests/conftest.py` — reuse for all new tests.

Git repo fixture pattern for new tests:
```python
@pytest.fixture
def tmp_git_repo(tmp_path):
    from git import Repo
    repo = Repo.init(tmp_path)
    (tmp_path / "records").mkdir()
    return repo, tmp_path
```

---

## Sources

### Primary (HIGH confidence)
- Codebase direct inspection (`src/bagels/git/repository.py`, `src/bagels/config.py`, `src/bagels/managers/records.py`, `src/bagels/app.py`, `src/bagels/export/exporter.py`, `src/bagels/importer/importer.py`, `src/bagels/__main__.py`) — current implementation state
- `pyproject.toml` — exact dependency versions (textual>=1.0,<2.0, gitpython>=3.1,<4.0, pydantic>=2.0,<3.0, click>=8.0,<9.0)
- `tests/conftest.py` — existing test fixture patterns

### Secondary (MEDIUM confidence)
- gitpython 3.x documented API: `Repo`, `index.add()`, `index.commit()`, `remote.push()`, `remote.pull()`, `iter_commits()`, `is_dirty()`
- Textual 1.x `@work` decorator API: `thread=True` parameter, `exclusive=True` flag, `call_from_thread()`

### Tertiary (LOW confidence)
- None — all claims are verifiable from the codebase or well-documented stable APIs.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed, versions pinned in pyproject.toml, existing usage in codebase
- Architecture: HIGH — hook patterns and manager structure directly inspected; Textual worker and gitpython APIs are stable and documented
- Pitfalls: HIGH — derived from direct codebase analysis (delete export gap, lock contention), standard concurrency issues, and the existing export/import design

**Research date:** 2026-03-16
**Valid until:** 2026-06-16 (stable libraries, patterns unlikely to change)
