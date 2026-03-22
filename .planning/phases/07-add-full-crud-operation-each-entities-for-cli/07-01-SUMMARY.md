---
phase: 07-add-full-crud-operation-each-entities-for-cli
plan: "01"
subsystem: cli
tags: [crud, cli, accounts, persons, formatters, helpers]
dependency_graph:
  requires: []
  provides:
    - src/bagels/cli/_helpers.py
    - src/bagels/queries/formatters.py (format_persons, format_templates)
    - src/bagels/cli/accounts.py (add, show, update, delete subcommands)
    - src/bagels/cli/persons.py
  affects:
    - src/bagels/__main__.py (persons registration deferred to Plan 02)
tech_stack:
  added: []
  patterns:
    - resolve_entity: ID/slug resolution pattern for all entity CLI commands
    - confirm_delete: interactive delete confirmation with --force bypass
    - check_cascade_records: linked record counting before delete
    - echo_entity: single-entity format+echo helper
key_files:
  created:
    - src/bagels/cli/_helpers.py
    - src/bagels/cli/persons.py
  modified:
    - src/bagels/queries/formatters.py
    - src/bagels/cli/accounts.py
decisions:
  - "Lazy imports inside command functions to avoid circular imports (model classes not imported at module level in _helpers.py)"
  - "Cancellation and error messages use click.echo(..., err=True) for stderr; success messages go to stdout"
  - "persons registration in __main__.py deferred to Plan 02 to avoid parallel write conflicts"
metrics:
  duration_seconds: 135
  completed_date: "2026-03-23"
  tasks_completed: 3
  files_changed: 4
---

# Phase 07 Plan 01: CLI Shared Helpers, Formatter Extensions, and Accounts/Persons CRUD Summary

**One-liner:** Shared CLI helpers (resolve_entity, confirm_delete, check_cascade_records, echo_entity) with format_persons/format_templates in formatters.py plus full CRUD subcommands for accounts and persons.

## What Was Built

### Task 1: Shared CLI helpers and formatter extensions

Created `/src/bagels/cli/_helpers.py` with four reusable functions:

- `resolve_entity(session, model_class, identifier)` — tries integer ID first, falls back to slug query
- `confirm_delete(entity_name, entity_display, force)` — skip prompt if `--force`, else `click.confirm`
- `check_cascade_records(session, model_class_name, entity_id)` — counts linked records for Account/Category or linked splits for Person
- `echo_entity(entity_obj, format_fn, output_format)` — wraps single-entity list in formatter and echoes

Extended `/src/bagels/queries/formatters.py` with:

- `format_persons(persons, output_format)` — table with ID, Name, Slug columns; JSON/YAML via `_person_to_dict`
- `format_templates(templates, output_format)` — table with ID, Label, Amount, Account, Category, Income, Transfer; JSON/YAML via `_template_to_dict`
- `_person_to_dict(person)` — serializes id, name, slug
- `_template_to_dict(template)` — serializes all template fields with nested account/category dicts

### Task 2: Full CRUD for accounts CLI

Extended `/src/bagels/cli/accounts.py` with four new subcommands added to the existing `accounts` group:

- `accounts show <identifier>` — resolves by ID or slug, calculates balance, echoes formatted output
- `accounts add` — interactive prompts for missing `--name` and `--balance`; calls `create_account`
- `accounts update <identifier>` — field-level updates from non-None options; rejects empty updates
- `accounts delete <identifier>` — cascade count check, confirmation prompt, `--force` bypass, `--cascade` soft-delete of linked records; cancellation to stderr

### Task 3: Full CRUD for persons CLI

Created `/src/bagels/cli/persons.py` following the same module structure as accounts.py:

- `persons list` — queries active (non-deleted) persons, formats with `format_persons`
- `persons add` — interactive prompt when `--name` absent; calls `create_person`
- `persons show <identifier>` — ID/slug resolution via `resolve_entity`
- `persons update <identifier>` — requires `--name`; raises ClickException if no fields provided
- `persons delete <identifier>` — split count check via `check_cascade_records("Person", ...)`, `--force` and `--cascade` support; cascade soft-deletes records linked via splits

## Verification

All four import checks pass:

```
from bagels.cli._helpers import resolve_entity, confirm_delete, check_cascade_records, echo_entity  # OK
from bagels.queries.formatters import format_persons, format_templates  # OK
from bagels.cli.accounts import accounts  # commands: ['list', 'show', 'add', 'update', 'delete']
from bagels.cli.persons import persons   # commands: ['list', 'add', 'show', 'update', 'delete']
```

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | af22287 | feat(07-01): add shared CLI helpers and extend formatters for persons/templates |
| 2 | 5662fcb | feat(07-01): implement full CRUD subcommands for accounts CLI |
| 3 | 25b4e87 | feat(07-01): implement full CRUD CLI for persons entity |

## Self-Check: PASSED

Files verified:
- src/bagels/cli/_helpers.py — FOUND
- src/bagels/queries/formatters.py — FOUND (format_persons, format_templates, _person_to_dict, _template_to_dict)
- src/bagels/cli/accounts.py — FOUND (list, show, add, update, delete)
- src/bagels/cli/persons.py — FOUND (list, add, show, update, delete)

Commits verified:
- af22287 — FOUND
- 5662fcb — FOUND
- 25b4e87 — FOUND
