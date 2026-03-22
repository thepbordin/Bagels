---
phase: 07-add-full-crud-operation-each-entities-for-cli
plan: 04
subsystem: documentation, testing, requirements
tags: [skill.md, smoke-tests, requirements, crud, documentation]
dependency_graph:
  requires: [07-01, 07-02, 07-03]
  provides: [SKILL.md CRUD reference, CRUD smoke tests, CRUD-01..09 requirements]
  affects: [SKILL.md, tests/cli/test_crud.py, .planning/REQUIREMENTS.md]
tech_stack:
  added: []
  patterns: [pytest-class-based-smoke-tests, click-param-introspection]
key_files:
  created:
    - tests/cli/test_crud.py
  modified:
    - SKILL.md
    - .planning/REQUIREMENTS.md
decisions:
  - SKILL.md restructured Mutation Commands section to document both inline and batch records add
  - Smoke tests use Click command introspection (params list) rather than invoking commands, making them database-free
  - CRUD-01..09 formally defined and traced to Phase 7 in traceability table
metrics:
  duration_seconds: 420
  completed_date: "2026-03-23"
  tasks_completed: 3
  files_modified: 3
---

# Phase 7 Plan 4: Documentation, Smoke Tests, and Requirements Summary

**One-liner:** SKILL.md fully documents all 5-entity CRUD CLI commands with flags and examples; 16 smoke tests verify command registration via Click introspection; CRUD-01 through CRUD-09 formally defined in REQUIREMENTS.md.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Update SKILL.md with CRUD command documentation | 499ec71 | SKILL.md |
| 2 | Create smoke tests for CRUD command registration | 1b9d042 | tests/cli/test_crud.py |
| 3 | Define CRUD-01 through CRUD-09 in REQUIREMENTS.md | f2375d4 | .planning/REQUIREMENTS.md |

## What Was Built

### SKILL.md Updates

Restructured the Mutation Commands section to document both inline and batch modes for `bagels records add`, then added a new `## Entity CRUD Commands` section covering:

- **Accounts**: add, show, update, delete (with --force, --cascade flags)
- **Categories**: list, show, add, update, delete (with --force, --cascade flags)
- **Persons**: list, add, show, update, delete (with --force, --cascade flags)
- **Templates**: list, add, show, update, delete (with --force flag; hard delete noted)

Added workflow pattern 5 ("Create a Record from CLI Flags") and four new Tips items covering IDENTIFIER semantics, --format support, --force, and --cascade behavior.

### Smoke Tests (tests/cli/test_crud.py)

16 tests across 5 test classes using Click command introspection:
- `TestAccountsCRUD` (3 tests): subcommand registration, add params (name/balance), delete params (cascade/force)
- `TestCategoriesCRUD` (3 tests): subcommand registration, add params (name/nature), delete params (cascade/force)
- `TestPersonsCRUD` (3 tests): subcommand registration, CLI top-level registration, delete params (cascade/force)
- `TestTemplatesCRUD` (3 tests): subcommand registration, CLI top-level registration, add required options
- `TestRecordsCRUD` (4 tests): subcommand registration, add inline options, update identifier, delete force

All 16 tests pass. Tests are database-free (introspect Click command objects only).

### REQUIREMENTS.md

Added `## CLI CRUD Mutations (Phase 7)` section with CRUD-01 through CRUD-09 definitions. Added all 9 to the traceability table mapped to Phase 7 with "Planned" status. Updated coverage total from 60 to 69.

## Verification

```
uv run pytest tests/cli/test_crud.py -v  # 16 passed in 0.06s
grep -c "bagels accounts add" SKILL.md    # 3
grep -c "bagels records delete" SKILL.md  # 3
grep "CRUD-09" .planning/REQUIREMENTS.md  # 2 matches (definition + traceability)
```

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- SKILL.md exists and contains `bagels accounts add`: FOUND
- tests/cli/test_crud.py exists with 16 tests: FOUND
- .planning/REQUIREMENTS.md contains CRUD-01 through CRUD-09: FOUND
- Commits 499ec71, 1b9d042, f2375d4 exist: FOUND
