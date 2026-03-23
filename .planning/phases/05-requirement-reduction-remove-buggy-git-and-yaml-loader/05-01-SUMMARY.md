---
phase: 05-requirement-reduction-remove-buggy-git-and-yaml-loader
plan: "01"
subsystem: cli
tags: [sqlite, cli, startup, config, deprecation]
requires: []
provides:
  - Removed git/export/import command wiring from top-level CLI
  - Removed startup YAML sync worker invocation from app mount path
  - Added one-time legacy Git/YAML sync deprecation warning guard
affects: [phase-05-02, phase-05-03, testing]
tech-stack:
  added: []
  patterns: [sqlite-only-runtime, compatibility-warning]
key-files:
  created: []
  modified:
    - src/bagels/__main__.py
    - src/bagels/app.py
    - src/bagels/config.py
    - src/bagels/cli/__init__.py
key-decisions:
  - "Removed sync commands from routing instead of keeping hidden aliases to enforce unknown-command behavior at the CLI boundary."
  - "Kept legacy git config parsing for backward compatibility but emit only one persisted warning."
patterns-established:
  - "Startup path must not perform data synchronization side effects."
  - "Deprecated behavior should degrade with a single warning, not repeated startup noise."
requirements-completed: [REDUCE-01, REDUCE-02, REDUCE-03]
duration: 45min
completed: 2026-03-21
---

# Phase 5 Plan 01 Summary

**Top-level runtime entrypoints now boot and route strictly in SQLite-only mode with no startup Git/YAML sync path.**

## Performance

- **Duration:** 45 min
- **Started:** 2026-03-21T18:10:00+07:00
- **Completed:** 2026-03-21T18:55:00+07:00
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Removed `git`, `export`, and `import` from top-level command registration.
- Removed `run_startup_import` startup worker path from `App.on_mount()`.
- Added persisted one-time deprecation warning for legacy sync-focused `git.*` config values.

## Task Commits

Execution was performed inline without per-task commits in this working session.

1. **Task 1: Remove sync command registration from top-level CLI** - `N/A` (inline)
2. **Task 2: Remove startup YAML sync execution path** - `N/A` (inline)
3. **Task 3: Add one-time deprecation warning for legacy sync config** - `N/A` (inline)

## Files Created/Modified
- `src/bagels/__main__.py` - Removed sync command imports and registrations.
- `src/bagels/app.py` - Removed startup YAML sync worker invocation and implementation.
- `src/bagels/config.py` - Added one-time legacy sync warning and persisted guard flag.
- `src/bagels/cli/__init__.py` - Removed sync command re-exports.

## Decisions Made
- Chose unknown-command behavior at the CLI root (not deprecated aliases) so users get immediate command removal feedback.
- Preserved `git.*` config model fields to avoid breaking existing config files.

## Deviations from Plan

None - plan executed as specified.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness
- Runtime no longer invokes sync paths, enabling safe removal of manager side effects and sync-only modules in Plan 05-02.

---
*Phase: 05-requirement-reduction-remove-buggy-git-and-yaml-loader*
*Completed: 2026-03-21*
