# Phase 7: Add Full CRUD Operations for Each Entity via CLI - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Expose create, read (show/list), update, and delete CLI commands for all 5 entities (accounts, categories, persons, records, templates). The manager layer already has full CRUD — this phase wires it to Click CLI commands with consistent patterns.

</domain>

<decisions>
## Implementation Decisions

### Entity scope
- All 5 entities get full CRUD: accounts, categories, persons, records, templates
- `bagels persons` and `bagels templates` are new top-level command groups (registered in `__main__.py`)
- Consistent with existing pattern: `bagels accounts`, `bagels categories`, `bagels records`
- `bagels records add` keeps existing `--from-yaml` batch import AND adds inline flag-based single record creation

### Input method
- Primary input via CLI flags (e.g. `--name 'Savings' --balance 1000`)
- Interactive fallback: if required fields are missing from flags, prompt the user for those missing required fields only
- Optional fields are never prompted — use flag or accept default
- Target for update/delete: accept integer ID or slug string as positional argument (e.g. `bagels accounts update 3 --name 'New'` or `bagels accounts update my-slug --name 'New'`)

### Delete behavior
- Soft delete only (set `deletedAt` timestamp) — matches existing manager pattern and TUI behavior
- **Exception: records use hard delete** (`session.delete`) — the existing `delete_record` manager already does hard delete; CLI wraps it as-is rather than diverging from the manager
- Confirmation prompt by default: `Delete account 'Savings'? [y/N]`
- `--force` / `-f` flag skips confirmation (enables scripting/automation)
- Cascade protection: block delete when entity has linked records, show error with count and suggest `--cascade` flag
- `--cascade` flag soft-deletes the entity AND all associated records

### Output & feedback
- Create/update: echo the created/updated entity in current `--format` (table/json/yaml)
- Delete: confirmation message only (e.g. `Deleted account 'Savings' (ID: 3)`)
- All create/update commands support `--format` / `-f` flag consistent with existing list/show commands
- Error output to stderr, success output to stdout

### Claude's Discretion
- Exact flag names for each entity's fields (follow field naming conventions from models)
- Which fields are required vs optional for each entity's create command
- How to handle the interactive prompt UX (Click's `click.prompt` is fine)
- Formatter function organization — extend existing `queries/formatters.py` or create per-entity formatters

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing CLI patterns
- `src/bagels/cli/records.py` — Most complete CLI module; has list, show, add with _open_session() pattern
- `src/bagels/cli/accounts.py` — Simple list-only module; shows _open_session() and format_accounts usage
- `src/bagels/cli/categories.py` — Tree display with manual table rendering

### Manager layer (CRUD already implemented)
- `src/bagels/managers/accounts.py` — create_account, get_all_accounts, update_account, delete_account
- `src/bagels/managers/categories.py` — create_category, get_all_categories_tree, update_category, delete_category
- `src/bagels/managers/persons.py` — create_person, get_all_persons, update_person, delete_person
- `src/bagels/managers/records.py` — create_record, get_record_by_id, update_record, delete_record
- `src/bagels/managers/record_templates.py` — create_template, get_all_templates, update_template, delete_template

### Models (field definitions)
- `src/bagels/models/account.py` — Account fields: name, beginningBalance, description, hidden
- `src/bagels/models/category.py` — Category fields: name, nature, color, parentCategoryId
- `src/bagels/models/person.py` — Person fields: name
- `src/bagels/models/record.py` — Record fields: label, amount, date, accountId, categoryId, isIncome, isTransfer
- `src/bagels/models/record_template.py` — RecordTemplate fields

### Entry point and registration
- `src/bagels/__main__.py` — Where CLI command groups are registered via cli.add_command()

### Formatting
- `src/bagels/queries/formatters.py` — Shared format_records, format_accounts, to_json, to_yaml utilities

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_open_session()` pattern: Used in all CLI modules for DB session management with engine disposal
- `queries/formatters.py`: Has format_records, format_accounts, to_json, to_yaml — extend for persons, categories, templates
- `export/slug_generator.py`: generate_record_slug for auto-generating record slugs on create
- Click framework patterns: `@click.group()`, `@click.option()`, `@click.argument()` consistently used

### Established Patterns
- All CLI modules import `load_config` + `init_db` at command execution time (lazy loading)
- Session pattern: create engine from `database_file()`, configure Session, use try/finally to close
- Format flag: `--format` / `-f` with choices `["table", "json", "yaml"]` defaulting to `"table"`
- Managers use `session = Session()` with `try/finally: session.close()` — CLI must pass session or let managers create their own

### Integration Points
- `__main__.py` line 127-145: Where new command groups (persons, templates) get registered
- Each CLI module is a separate file in `src/bagels/cli/`
- Existing `accounts`, `categories`, `records` modules need new subcommands (add, update, delete, show)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches following existing codebase patterns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-add-full-crud-operation-each-entities-for-cli*
*Context gathered: 2026-03-22*
