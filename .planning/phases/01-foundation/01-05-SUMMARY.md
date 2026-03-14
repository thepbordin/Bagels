---
phase: 01-foundation
plan: 05
subsystem: CLI Interface
tags: [cli, git, export, import, initialization]
requirements_met: [GIT-01, CMD-01, CMD-02, CMD-03, FMT-01, FMT-02, FMT-03, FMT-05]
dependency_graph:
  requires:
    - "01-02 (export functions)"
    - "01-04 (import functions)"
  provides:
    - "CLI commands for user interaction"
    - "Git repository management"
  affects:
    - "User workflow for Git-based data tracking"
tech_stack:
  added:
    - "GitPython 3.1.46 for Git repository management"
  patterns:
    - "Click command framework"
    - "Rich progress bars"
    - "Session management via SQLAlchemy Session factory"
key_files:
  created:
    - "src/bagels/git/__init__.py"
    - "src/bagels/git/repository.py"
    - "src/bagels/cli/__init__.py"
    - "src/bagels/cli/export.py"
    - "src/bagels/cli/import.py"
    - "src/bagels/cli/init.py"
  modified:
    - "src/bagels/__main__.py"
    - "pyproject.toml"
decisions:
  - "Used importlib to avoid Python 'import' keyword conflict in CLI module"
  - "Session created per command execution for proper database connection management"
  - "Progress bars use Rich SpinnerColumn for consistent UX"
metrics:
  duration: "8 minutes"
  completed: "2026-03-14T17:07:00Z"
  tasks_completed: 4
  files_created: 6
  files_modified: 2
  commits: 2
---

# Phase 01 Plan 05: CLI Interface for Export/Import and Git Integration Summary

Complete CLI interface for YAML export/import and Git initialization, providing user-facing access to the foundation features implemented in previous plans. Users can now initialize Git repositories, export SQLite data to YAML, and import YAML files back into the database through simple commands.

## What Was Built

### Git Repository Manager (`src/bagels/git/`)
- **repository.py**: Core Git repository management functions
  - `initialize_git_repo()`: Creates new Git repo or detects existing one
  - `create_gitignore()`: Creates .gitignore with SQLite exclusions (*.db, backups/)
- Returns boolean indicating if repo was newly created
- Uses GitPython 3.1.46 for Git operations

### CLI Commands (`src/bagels/cli/`)

#### 1. `bagels export` Command
- Exports all SQLite entities to YAML files
- Progress bars show export status for each entity type
- Verbose mode (`-v`) displays detailed file paths
- Exports: accounts, categories, persons, templates, records (by month)
- Uses SQLAlchemy Session for database operations
- Green checkmark on success

#### 2. `bagels import` Command
- Imports YAML files back into SQLite database
- **Validation first**: Validates all YAML files before importing
- **Dry-run mode** (`--dry-run`): Validates without making changes
- Verbose mode shows import/update counts per entity type
- Processes all monthly record files
- Clear error messages for validation failures
- Auto-backup created before import (from importer.py)

#### 3. `bagels init` Command
- Initializes Git repository in data directory
- Creates .gitignore with SQLite exclusions
- Creates initial commit for new repositories
- `--force` flag for reinitialization
- Displays next steps (export, add remote, push)

### Command Registration
- All commands registered in `__main__.py` Click group
- Used `importlib` to work around Python's `import` keyword conflict
- Commands accessible via `bagels export`, `bagels import`, `bagels init`

## Command Usage Examples

```bash
# Initialize Git repository in data directory
bagels init

# Export all data to YAML (verbose)
bagels export --verbose

# Import YAML files with validation only (dry-run)
bagels import --dry-run --verbose

# Import YAML files
bagels import --verbose

# Reinitialize existing Git repository
bagels init --force
```

## Deviations from Plan

### Auto-fixed Issues

**None** - Plan executed exactly as written. All tasks completed without issues or blockers.

## Technical Implementation Notes

### Session Management
- Commands create SQLAlchemy Session using `Session = sessionmaker(bind=db_engine)`
- Session closed after command completion
- Session passed to export/import functions for query operations

### Importlib Workaround
- Python's `import` keyword prevented normal import: `from bagels.cli import import`
- Solution: Used `importlib.import_module("bagels.cli.import")` in `__init__.py`
- Maintains clean API while avoiding syntax errors

### Error Handling
- All commands use try/except with ClickException
- Progress bars updated with error messages
- User-friendly error messages displayed

### Progress Bar UX
- Uses Rich's SpinnerColumn and TextColumn
- Transient progress bars (disappear after completion)
- Descriptive task updates for each operation

## Verification Results

All commands verified successfully:
- ✓ `bagels export` registered with proper help text
- ✓ `bagels import` registered with --dry-run option
- ✓ `bagels init` registered with --force option
- ✓ Git repository functions tested in temporary directory
- ✓ Commands follow existing Click framework patterns
- ✓ Progress bars display correctly
- ✓ Error handling tested

## Phase 1 Completion

This plan completes **Phase 1: Foundation**. All requirements met:

**Requirements Delivered:**
- **GIT-01**: Git repository initialization ✓
- **CMD-01**: bagels export command ✓
- **CMD-02**: bagels import command ✓
- **CMD-03**: bagels init command ✓
- **FMT-01, FMT-02, FMT-03, FMT-05**: YAML format support ✓

**Success Criteria Achieved:**
1. ✓ User can export all SQLite entities to YAML files
2. ✓ User can import YAML files back to SQLite
3. ✓ YAML files organized with monthly grouping and slug-based IDs
4. ✓ User can initialize Git repository
5. ✓ User can manually export/import data via CLI

**Phase 1 Plans Complete:** 6/6 (100%)
- 01-01: Test Infrastructure
- 01-01b: Record Export Tests (TDD RED)
- 01-02: Export Functions (TDD GREEN)
- 01-03: Slug Generator
- 01-04: Import Functions
- 01-05: CLI Interface (this plan)

## Next Steps

Phase 1 complete. Recommended next phases:
- **Phase 2**: CLI query interface and LLM integration
- **Phase 3**: Automated Git sync
- **Phase 4**: TUI integration with YAML data

Users can now:
1. Run `bagels init` to initialize Git repository
2. Run `bagels export` to create YAML files
3. Commit YAML files to Git
4. Push to remote repository
5. Pull changes from collaborators
6. Run `bagels import` to merge changes into SQLite
