# Phase 1: Foundation - Context

**Gathered:** 2026-03-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish YAML as canonical data format with bidirectional SQLite sync and Git repository initialization. Users can export all SQLite entities to human-readable YAML files and import YAML files back into the database with complete data fidelity. YAML files are organized in `data/` directory with monthly record grouping and slug-based IDs.

</domain>

<decisions>
## Implementation Decisions

### Import Conflict Handling
- **Merge by ID strategy**: Records matching by slug ID update existing SQLite data, new records are added
- **YAML is authoritative**: When merging, records that exist in both SQLite and YAML are updated with YAML data (allows Git changes to propagate)
- **Fail fast on broken references**: Import fails immediately if YAML refers to non-existent categories/persons/accounts (referential integrity enforced)
- **Auto backup before import**: Automatic backup to `~/.local/share/bagels/backups/` before every import operation

### YAML Data Structure
- **Dict keyed by slug ID**: Entities structured as `accounts: {acc_savings: {name: Savings, ...}, ...}` for clearer diffs and easier manual editing
- **Include all fields**: YAML exports include complete field data plus metadata (createdAt, updatedAt timestamps)
- **Slug-based relationship references**: Foreign keys use slug IDs (e.g., `accountId: acc_savings`) for human-readable diffs
- **Preserve human comments**: YAML comments are preserved during export/import cycles (users can annotate their financial data)

### Data Validation on Import
- **Validate all then prompt**: Validate entire YAML file first, report all errors together, then ask user to continue or abort
- **Float for monetary values**: Amounts stored as IEEE 754 floats in YAML (standard approach, matches SQLite REAL type)
- **Strict schema validation**: All mandatory fields required, validation fails on missing or malformed data
- **List all errors**: Each validation error printed to console with file/line reference for maximum clarity

### Claude's Discretion
- Exact backup file naming scheme (timestamp-based or sequential)
- Progress bar design for export operations
- Verbose mode output format and detail level
- Comment preservation implementation (YAML library capabilities)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **SQLAlchemy 2.0 ORM** — Models defined in `src/bagels/models/` with declarative base pattern
- **Click 8.0 CLI framework** — Already used for `bagels` command in `src/bagels/__main__.py`
- **YAML 6.0 library** — Already available for config files, can be reused for data export/import
- **Pydantic 2.0** — Data validation and configuration models in `src/bagels/config.py`

### Established Patterns
- **Manager classes** — Business logic in `src/bagels/managers/` (accounts.py, categories.py, etc.)
- **Model timestamp fields** — Automatic `createdAt`, `updatedAt`, `deletedAt` on all models
- **Pydantic validation** — Configuration uses Pydantic for schema validation and error messages
- **Absolute imports** — All imports use absolute paths from project root (e.g., `from bagels.models.account import Account`)

### Integration Points
- **CLI entry point** — `src/bagels/__main__.py` contains Click CLI setup, new commands added here
- **Database session** — SQLAlchemy session management already exists, can be reused for bulk import/export
- **Model layer** — Export/import reads/writes SQLAlchemy models directly
- **File locations** — `src/bagels/locations.py` handles data directory paths, extend for YAML file paths

</code_context>

<specifics>
## Specific Ideas

- "I like how Git shows clear diffs — YAML structure should make financial changes obvious at a glance"
- Slug-based IDs chosen for mergeability: "r_2026-03-14_001" format lets multiple devices generate IDs without UUID conflicts
- Merge by ID strategy enables workflow: TUI edits → export → Git commit → pull merge → import → see both local and remote changes
- Fail-fast on broken refs prevents silent data corruption: better to abort import than create orphaned records

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-03-14*
