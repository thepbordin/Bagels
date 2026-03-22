# Roadmap: Bagels v1

**Milestone:** Git-trackable, LLM-accessible expense tracker
**Created:** 2026-03-14
**Granularity:** Coarse
**Phases:** 6

## Phases

- [ ] **Phase 1: Foundation** - YAML data format, bidirectional sync, and Git repository integration
- [ ] **Phase 2: CLI Query Layer** - Query interface and LLM context commands
- [x] **Phase 3: Automation** - Auto-export/import and Git auto-operations (completed 2026-03-15)
- [x] **Phase 4: Verification** - Testing and validation (completed 2026-03-19)
- [x] **Phase 5: Requirement Reduction** - Remove buggy Git/YAML runtime sync paths and stabilize SQLite-only behavior (completed 2026-03-21)
- [ ] **Phase 6: SKILL.md for LLM CLI Usage Documentation** - Self-contained LLM reference for all Bagels CLI commands

## Phase Details

### Phase 1: Foundation

**Goal:** Establish YAML as canonical data format with bidirectional SQLite sync and Git repository initialization

**Depends on:** Nothing

**Requirements:** DATA-01, DATA-02, DATA-03, DATA-04, DATA-05, DATA-06, FMT-01, FMT-02, FMT-03, FMT-05, GIT-01, CMD-01, CMD-02, CMD-03
**NOTE:** FMT-04 (comment preservation) de-scoped per technical decision - see 01-FMT04-DECISION.md

**Success Criteria** (what must be TRUE):
1. User can export all SQLite entities (accounts, categories, persons, templates, records) to human-readable YAML files
2. User can import YAML files back into SQLite database with complete data fidelity
3. YAML files are organized in `data/` directory with monthly record grouping and slug-based IDs
4. User can initialize data directory as Git repository with `bagels init` command
5. User can manually export and import data via `bagels export` and `bagels import` commands

**Plans:** 6

Plan Overview:
- **01-01-PLAN.md** — Create test infrastructure for entity export (accounts, categories, persons, templates) using TDD
- **01-01b-PLAN.md** — Create test infrastructure for record export with monthly grouping and slug generation using TDD
- **01-02-PLAN.md** — Implement YAML export functionality for all SQLite entities
- **01-03-PLAN.md** — Create test infrastructure for YAML import functionality (validation, merge-by-ID, referential integrity) using TDD
- **01-04-PLAN.md** — Implement YAML import functionality with validation and merge-by-ID strategy
- **01-05-PLAN.md** — Implement CLI commands for export/import operations and Git initialization

Plans:
- [ ] 01-01-PLAN.md — Test infrastructure for entity export (accounts, categories, persons, templates) - 4 test files
- [ ] 01-01b-PLAN.md — Test infrastructure for record export (monthly grouping, slug generation) - 2 test files
- [ ] 01-02-PLAN.md — Export functions for all entities with dict-based YAML structure
- [ ] 01-03-PLAN.md — Test infrastructure for import functionality (validation, merge-by-ID, referential integrity)
- [ ] 01-04-PLAN.md — Import functions with validation and merge-by-ID strategy
- [ ] 01-05-PLAN.md — CLI commands (bagels export, bagels import, bagels init) and Git repository manager

---

### Phase 2: CLI Query Layer

**Goal:** Provide comprehensive CLI interface for querying records, summaries, and LLM context dumps

**Depends on:** Phase 1 (Foundation)

**Requirements:** CLI-01, CLI-02, CLI-03, CLI-04, CLI-05, CLI-06, CLI-07, CLI-08, CLI-09, CLI-10, LLM-01, LLM-02, LLM-03, LLM-04, LLM-05

**Success Criteria** (what must be TRUE):
1. User can query records by month, category, and date range with table or JSON output
2. User can generate financial summaries and spending breakdowns by category or day
3. User can dump complete financial snapshot for LLM consumption via `bagels context --month`
4. User can view data schema via `bagels schema` commands for LLM context
5. All query commands support structured output formats (table, JSON, YAML)

**Plans:** 2/8 plans executed

---

### Phase 3: Automation

**Goal:** Automate YAML export/import lifecycle and Git operations for seamless sync

**Depends on:** Phase 1 (Foundation)

**Requirements:** DATA-07, DATA-08, GIT-02, GIT-03, GIT-04, GIT-05, GIT-06, GIT-07, GIT-08, CFG-01, CFG-02, CFG-03, CFG-04, CFG-05

**Success Criteria** (what must be TRUE):
1. YAML files auto-export on every record save/update/delete operation
2. YAML files auto-import on application startup to refresh SQLite database
3. Git auto-commits YAML changes with descriptive messages
4. User can sync with remote via `bagels git sync` (commit + push)
5. User can pull remote changes via `bagels git pull` and auto-import updated YAML
6. Optional auto-push to remote configured via config file
7. System auto-pulls remote changes on startup

**Plans:** 4/4 plans complete

Plans:
- [ ] 03-01-PLAN.md — GitConfig Pydantic model + git/operations.py (commit, push, pull, status, log helpers)
- [ ] 03-02-PLAN.md — Manager hooks for all 5 entities + export_records_for_month targeted helper
- [ ] 03-03-PLAN.md — bagels git CLI command group (sync, pull, status, log) registered in __main__.py
- [ ] 03-04-PLAN.md — Startup YAML import Textual worker with optional auto-pull in app.py

---

### Phase 4: Verification

**Goal:** Validate system reliability through comprehensive testing

**Depends on:** Phase 1 (Foundation), Phase 2 (CLI Query Layer), Phase 3 (Automation)

**Requirements:** TEST-01, TEST-02, TEST-03, TEST-04, TEST-05

**Success Criteria** (what must be TRUE):
1. Bidirectional sync maintains data integrity across multiple export/import cycles
2. Git merge conflicts resolve correctly with manual intervention
3. All CLI query commands produce valid output in table, JSON, and YAML formats
4. Auto-export triggers fire correctly on all CRUD operations
5. LLM context output includes all required financial data sections

**Plans:** 4/4 plans complete

Plans:
- [ ] 04-01-PLAN.md — Bidirectional sync integration tests (3 round-trip cycles, slug preservation, backup verification, corrupt YAML)
- [ ] 04-02-PLAN.md — Auto-export trigger integration tests (real DB + real temp dir, all 5 entity types, create/update/delete)
- [ ] 04-03-PLAN.md — Git conflict detection in run_full_import() + two-clone conflict simulation tests
- [ ] 04-04-PLAN.md — CLI output format tests (table/JSON/YAML) + LLM context section completeness tests

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/6 | Planning complete | - |
| 2. CLI Query Layer | 2/8 | In Progress|  |
| 3. Automation | 4/4 | Complete    | 2026-03-15 |
| 4. Verification | 4/4 | Complete    | 2026-03-19 |
| 5. Requirement Reduction | 3/3 | Complete | 2026-03-21 |
| 6. SKILL.md Documentation | 0/1 | Planned | - |
| 7. CLI CRUD Operations | 1/4 | In Progress|  |

## Coverage

**Total v1 Requirements:** 52 (FMT-04 de-scoped)
**Requirements Mapped:** 52 (100%)
**Phases:** 6

### Requirement Mapping Summary

| Category | Count | Phase |
|----------|-------|-------|
| Data Export/Import | 8 | Phase 1 (6), Phase 3 (2) |
| Git Sync | 8 | Phase 1 (1), Phase 3 (7) |
| CLI Query Interface | 10 | Phase 2 (10) |
| LLM Integration | 5 | Phase 2 (5) |
| Data Format | 4 | Phase 1 (4) - FMT-04 de-scoped |
| Configuration | 5 | Phase 3 (5) |
| CLI Commands | 3 | Phase 1 (3) |
| Testing | 5 | Phase 4 (5) |
| LLM CLI Documentation | 3 | Phase 6 (3) |
| CLI CRUD Operations | 9 | Phase 7 (9) |

**Traceability:** Full mapping maintained in REQUIREMENTS.md

### Phase 5: Requirement Reduction, remove buggy git and yaml loader

**Goal:** Remove buggy runtime Git/YAML sync behavior and rebaseline Bagels to SQLite-only operation with updated docs and tests.
**Requirements**: REDUCE-01, REDUCE-02, REDUCE-03, REDUCE-04
**Depends on:** Phase 4
**Plans:** 3/3 plans complete

Plans:
- [x] 05-01-PLAN.md — Remove sync command registration, startup YAML sync path, and add one-time deprecation warning
- [x] 05-02-PLAN.md — Remove manager export/commit hooks and retire sync-only CLI/git operations from runtime path
- [x] 05-03-PLAN.md — Rebaseline requirements/roadmap docs, replace obsolete sync tests, and pass full pytest gate

### Phase 6: SKILL.md for LLM CLI Usage Documentation

**Goal:** Create a self-contained SKILL.md at the repository root that teaches any LLM how to use every Bagels CLI command with exact flags, examples, and workflow patterns.
**Requirements**: DOC-01, DOC-02, DOC-03
**Depends on:** Phase 5
**Plans:** 1 plan

Plans:
- [ ] 06-01-PLAN.md — Write complete SKILL.md with CLI command reference, flag tables, examples, and four LLM workflow patterns

### Phase 7: Add Full CRUD Operations for Each Entity via CLI

**Goal:** Expose create, show, update, and delete CLI commands for all 5 entities (accounts, categories, persons, records, templates) with consistent patterns, interactive prompts, and delete safeguards.
**Requirements**: CRUD-01, CRUD-02, CRUD-03, CRUD-04, CRUD-05, CRUD-06, CRUD-07, CRUD-08, CRUD-09
**Depends on:** Phase 6
**Plans:** 1/4 plans executed

Plans:
- [ ] 07-01-PLAN.md — Shared CLI helpers, formatter extensions, and full CRUD for accounts + persons
- [ ] 07-02-PLAN.md — Full CRUD for categories + templates with FK validation
- [ ] 07-03-PLAN.md — Inline record creation, update, and delete commands
- [ ] 07-04-PLAN.md — SKILL.md CRUD documentation update and smoke tests

---
*Roadmap created: 2026-03-14*
*Plans created for Phase 1: 2026-03-14*
*Plan split (01-01 -> 01-01 + 01-01b): 2026-03-14*
*FMT-04 de-scoped: 2026-03-14*
*Plans created for Phase 3: 2026-03-16*
*Plans created for Phase 4: 2026-03-19*
*Plans created for Phase 5: 2026-03-21*
*Plans created for Phase 6: 2026-03-22*
*Plans created for Phase 7: 2026-03-22*

### Phase 04.1: fix test errors try to run uv run pytest investigate & FIX (INSERTED)

**Goal:** [Urgent work - to be planned]
**Requirements**: TBD
**Depends on:** Phase 4
**Plans:** 0 plans

Plans:
- [ ] TBD (run /gsd:plan-phase 04.1 to break down)
