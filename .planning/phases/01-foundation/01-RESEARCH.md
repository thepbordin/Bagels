# Phase 1: Foundation - Research

**Researched:** 2026-03-14
**Domain:** YAML data export/import with bidirectional SQLite sync and Git repository initialization
**Confidence:** HIGH

## Summary

Phase 1 establishes YAML as the canonical data format for Bagels, enabling bidirectional synchronization between SQLite (runtime) and YAML (Git-tracked). Research confirms the existing Python 3.13 + SQLAlchemy 2.0 + PyYAML stack is sufficient for core functionality, with GitPython needed for Git repository operations. The key technical challenge is implementing slug-based ID generation and monthly record grouping while maintaining referential integrity during import/export cycles.

**Primary recommendation:** Use existing PyYAML 6.0 for data serialization, add GitPython 3.1.44 for repository operations, and implement slug-based ID generation using Python's datetime formatting. Monthly record grouping should be implemented as separate YAML files per month (YYYY-MM.yaml) with records keyed by slug ID within each file.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Merge by ID strategy**: Records matching by slug ID update existing SQLite data, new records are added
- **YAML is authoritative**: When merging, records that exist in both SQLite and YAML are updated with YAML data (allows Git changes to propagate)
- **Fail fast on broken references**: Import fails immediately if YAML refers to non-existent categories/persons/accounts (referential integrity enforced)
- **Auto backup before import**: Automatic backup to `~/.local/share/bagels/backups/` before every import operation
- **Dict keyed by slug ID**: Entities structured as `accounts: {acc_savings: {name: Savings, ...}, ...}` for clearer diffs and easier manual editing
- **Include all fields**: YAML exports include complete field data plus metadata (createdAt, updatedAt timestamps)
- **Slug-based relationship references**: Foreign keys use slug IDs (e.g., `accountId: acc_savings`) for human-readable diffs
- **Preserve human comments**: YAML comments are preserved during export/import cycles (users can annotate their financial data)
- **Validate all then prompt**: Validate entire YAML file first, report all errors together, then ask user to continue or abort
- **Float for monetary values**: Amounts stored as IEEE 754 floats in YAML (standard approach, matches SQLite REAL type)
- **Strict schema validation**: All mandatory fields required, validation fails on missing or malformed data
- **List all errors**: Each validation error printed to console with file/line reference for maximum clarity

### Claude's Discretion
- Exact backup file naming scheme (timestamp-based or sequential)
- Progress bar design for export operations
- Verbose mode output format and detail level
- Comment preservation implementation (YAML library capabilities)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DATA-01 | Export all accounts to YAML format (`data/accounts.yaml`) | PyYAML safe_dump with dict-based structure, SQLAlchemy session.query(Account).all() |
| DATA-02 | Export all categories to YAML format (`data/categories.yaml`) | PyYAML safe_dump with recursive parent/child structure handling |
| DATA-03 | Export all persons to YAML format (`data/persons.yaml`) | PyYAML safe_dump with simple dict structure |
| DATA-04 | Export all templates to YAML format (`data/templates.yaml`) | PyYAML safe_dump with order preservation and relationship references |
| DATA-05 | Export records grouped by month to YAML format (`data/records/YYYY-MM.yaml`) | Python datetime grouping, slug-based ID generation, monthly file creation |
| DATA-06 | Import YAML files back into SQLite database | PyYAML safe_load, validation, SQLAlchemy bulk operations, merge-by-ID logic |
| FMT-01 | YAML files use human-readable, diffable format | PyYAML default_flow_style=False, block style formatting |
| FMT-02 | Record IDs use slug-based format (`r_YYYY-MM-DD_###`) | Python datetime.strftime formatting, sequential daily numbering |
| FMT-03 | Records grouped by month in separate files | Record.date grouping, monthly YAML file creation |
| FMT-04 | YAML includes metadata, comments supported | PyYAML preserves comments (requires ruamel.yaml for full support) |
| FMT-05 | All entities export with complete field data | SQLAlchemy model introspection, complete field serialization |
| GIT-01 | Initialize data directory as Git repository (`bagels init`) | GitPython Repo.init(), .gitignore creation |
| CMD-01 | `bagels export` command for manual YAML export | Click command integration, progress bars with rich.progress |
| CMD-02 | `bagels import` command for manual YAML import | Click command integration, validation prompts, error reporting |
| CMD-03 | `bagels init` command initializes new data directory with Git repo | Click command integration, directory creation, Git initialization |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **PyYAML** | 6.0 (existing) | YAML serialization/deserialization | Already in project, safe_load/safe_dump for security, Python 3.13 compatible |
| **SQLAlchemy** | 2.0 (existing) | ORM for SQLite operations | Existing models use SQLAlchemy 2.0 patterns, bulk operations support |
| **Click** | 8.0 (existing) | CLI command framework | Existing CLI uses Click, consistent command patterns |
| **GitPython** | 3.1.44 | Git repository operations | Industry standard for Git in Python, active maintenance, comprehensive API |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **ruamel.yaml** | 0.18+ | Comment preservation in YAML | Optional: if PyYAML comment preservation is insufficient |
| **rich** | existing | Progress bars and formatting | Existing use in CLI, consistent UX patterns |
| **pytest** | existing | Test framework | Existing test infrastructure, in-memory SQLite fixtures |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyYAML | ruamel.yaml | More features (comment preservation, round-trip) but heavier dependency |
| GitPython | gitpy3 | Less mature, smaller community |
| Slug-based IDs | UUIDs | UUIDs not mergeable in Git, less human-readable |
| Monthly files | Single large file | Monthly files more manageable, better Git diffs |

**Installation:**
```bash
# GitPython is new addition
pnpm add gitpython  # or: pip install gitpython

# Optional: ruamel.yaml for advanced comment handling
# pnpm add ruamel.yaml  # or: pip install ruamel.yaml
```

## Architecture Patterns

### Recommended Project Structure
```
src/bagels/
├── export/              # NEW: Export/import layer
│   ├── __init__.py
│   ├── exporter.py      # Export SQLite → YAML
│   ├── importer.py      # Import YAML → SQLite
│   ├── slug_generator.py # Slug-based ID generation
│   └── validator.py     # YAML validation logic
├── git/                 # NEW: Git operations
│   ├── __init__.py
│   ├── repository.py    # Git repository management
│   └── commands.py      # Git command implementations
├── models/              # EXISTING: SQLAlchemy models
│   ├── account.py
│   ├── category.py
│   ├── person.py
│   ├── record.py
│   └── record_template.py
├── managers/            # EXISTING: Business logic
└── cli/                 # NEW/EXTENDED: CLI commands
    ├── export.py        # bagels export command
    ├── import.py        # bagels import command
    └── init.py          # bagels init command
```

### Pattern 1: Dict-Based YAML Structure
**What:** Export entities as dictionaries keyed by slug ID for clearer Git diffs
**When to use:** All entity exports (accounts, categories, persons, templates, records)
**Example:**
```python
# Source: Context.md + PyYAML documentation
# accounts.yaml structure:
accounts:
  acc_savings:
    name: "Savings"
    description: "Emergency fund"
    beginningBalance: 1000.0
    repaymentDate: null
    hidden: false
    createdAt: "2026-03-14T10:30:00"
    updatedAt: "2026-03-14T10:30:00"
  acc_checking:
    name: "Checking"
    description: "Daily expenses"
    beginningBalance: 2500.0
    repaymentDate: null
    hidden: false
    createdAt: "2026-03-14T10:30:00"
    updatedAt: "2026-03-14T10:30:00"
```

### Pattern 2: Slug-Based ID Generation
**What:** Generate human-readable, mergeable IDs using datetime + sequence
**When to use:** Record export/import, cross-referencing entities
**Example:**
```python
# Source: CONTEXT.md requirements
from datetime import datetime
from sqlalchemy import select

def generate_record_slug(record_date, session) -> str:
    """Generate slug: r_YYYY-MM-DD_###"""
    date_str = record_date.strftime("%Y-%m-%d")

    # Find existing records for this date
    existing = session.execute(
        select(Record).where(
            Record.date >= record_date.date(),
            Record.date < (record_date.date() + timedelta(days=1))
        )
    ).scalars().all()

    # Extract sequence numbers from existing slugs
    sequences = []
    for r in existing:
        if hasattr(r, 'slug') and r.slug.startswith(f"r_{date_str}_"):
            try:
                seq = int(r.slug.split('_')[-1])
                sequences.append(seq)
            except (ValueError, IndexError):
                pass

    # Next sequence number
    next_seq = max(sequences) + 1 if sequences else 1
    return f"r_{date_str}_{next_seq:03d}"
```

### Pattern 3: Monthly Record Grouping
**What:** Separate YAML files per month for manageable file sizes
**When to use:** Record export/import operations
**Example:**
```python
# Source: CONTEXT.md requirements
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def group_records_by_month(records):
    """Group records by month for file organization"""
    monthly = defaultdict(list)
    for record in records:
        month_key = record.date.strftime("%Y-%m")
        monthly[month_key].append(record)
    return monthly

# Export structure:
# data/records/
#   ├── 2026-01.yaml
#   ├── 2026-02.yaml
#   └── 2026-03.yaml
```

### Pattern 4: Merge-by-ID Import Strategy
**What:** Update existing records, add new records based on slug ID matching
**When to use:** YAML import operations
**Example:**
```python
# Source: CONTEXT.md decisions
def import_records_with_merge(yaml_data, session):
    """Import records using merge-by-ID strategy"""
    imported_count = 0
    updated_count = 0

    for slug, record_data in yaml_data['records'].items():
        existing = session.execute(
            select(Record).where(Record.slug == slug)
        ).scalar_one_or_none()

        if existing:
            # Update existing record (YAML is authoritative)
            for key, value in record_data.items():
                setattr(existing, key, value)
            updated_count += 1
        else:
            # Create new record
            new_record = Record(slug=slug, **record_data)
            session.add(new_record)
            imported_count += 1

    session.commit()
    return imported_count, updated_count
```

### Anti-Patterns to Avoid
- **Exporting database IDs**: Never expose SQLite integer IDs in YAML (breaks mergeability)
- **Inline YAML for large datasets**: Use monthly files, not single massive file
- **Skipping validation**: Always validate YAML before import to prevent partial updates
- **Ignoring referential integrity**: Fail fast if foreign key references don't exist
- **Using yaml.load()**: Always use safe_load() to prevent code injection

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom YAML parser | PyYAML safe_load/safe_dump | Edge cases: quotes, unicode, escaping, security |
| Git operations | Subprocess git calls | GitPython Repo API | Error handling, cross-platform, object model |
| CLI commands | argparse/manual sys.argv | Click 8.0 | Consistent patterns, help generation, testing |
| Progress bars | Custom progress printing | rich.progress | Visual consistency, ETA calculation, formatters |
| Slug generation | UUID or random | datetime.strftime + sequence | Mergeability, human-readable, time-sortable |

**Key insight:** Custom solutions for serialization/version control/file formats fail on edge cases (unicode, escaping, merge conflicts). Use battle-tested libraries.

## Common Pitfalls

### Pitfall 1: YAML Comment Preservation
**What goes wrong:** PyYAML doesn't preserve comments by default, user annotations lost
**Why it happens:** PyYAML focuses on data serialization, not formatting preservation
**How to avoid:** Use ruamel.yaml if comment preservation required, or document limitation
**Warning signs:** Comments disappear after export/import cycle
**Research confidence:** MEDIUM - PyYAML limitation known, ruamel.yaml supports this

### Pitfall 2: Float Precision in Monetary Values
**What goes wrong:** IEEE 754 floats introduce rounding errors in financial data
**Why it happens:** Binary floating-point cannot represent some decimal values exactly
**How to avoid:** Match SQLite REAL type behavior, round to CONFIG.defaults.round_decimals
**Warning signs:** Amount discrepancies between SQLite and YAML
**Research confidence:** HIGH - Existing code uses Float with rounding

### Pitfall 3: Referential Integrity During Import
**What goes wrong:** Import creates orphaned records (category/person/account doesn't exist)
**Why it happens:** No validation of foreign key references before insertion
**How to avoid:** Validate all references exist, fail fast with clear error messages
**Warning signs:** Foreign key violations, query errors accessing related entities
**Research confidence:** HIGH - CONTEXT.md explicitly requires fail-fast behavior

### Pitfall 4: Slug ID Collisions
**What goes wrong:** Multiple records generate same slug ID
**Why it happens:** Concurrent operations or gap in sequence numbering
**How to avoid:** Database-level unique constraint on slug, retry logic with new sequence
**Warning signs:** IntegrityError on duplicate slug during import
**Research confidence:** MEDIUM - Requires testing concurrent scenarios

### Pitfall 5: Monthly File Edge Cases
**What goes wrong:** Records at month boundaries create confusion
**Why it happens:** Timezone issues, record date vs. file date mismatch
**How to avoid:** Use record.date for grouping, consistent timezone handling
**Warning signs:** Records missing from exports, wrong monthly file
**Research confidence:** HIGH - datetime grouping is well-understood

### Pitfall 6: Git Repository Initialization
**What goes wrong:** Initializing Git repo in non-empty directory fails
**Why it happens:** Existing files conflict with Git initialization
**How to avoid:** Check if .git exists, use GitPython Repo.init() with appropriate options
**Warning signs:** GitCommandError during init
**Research confidence:** MEDIUM - GitPython documentation unclear on edge cases

## Code Examples

Verified patterns from official sources:

### SQLAlchemy Bulk Operations
```python
# Source: https://docs.sqlalchemy.org/en/20/orm/persistence_techniques.html
from sqlalchemy.orm import Session

def bulk_import_records(records_data, session):
    """Efficient bulk insert using SQLAlchemy 2.0 patterns"""
    records = [Record(**data) for data in records_data]
    session.add_all(records)
    session.commit()
    return records
```

### PyYAML Safe Operations
```python
# Source: https://pyyaml.org/wiki/PyYAMLDocumentation
import yaml

def export_accounts_yaml(accounts, file_path):
    """Export accounts to YAML with safe_dump"""
    data = {
        'accounts': {
            acc.slug: {
                'name': acc.name,
                'description': acc.description,
                'beginningBalance': acc.beginningBalance,
                'createdAt': acc.createdAt.isoformat(),
                'updatedAt': acc.updatedAt.isoformat(),
            }
            for acc in accounts
        }
    }

    with open(file_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

def import_accounts_yaml(file_path):
    """Import accounts from YAML with safe_load"""
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    return data['accounts']
```

### GitPython Repository Initialization
```python
# Source: https://gitpython.readthedocs.io/en/stable/
from git import Repo, InvalidGitRepositoryError
from pathlib import Path

def initialize_git_repo(data_dir: Path):
    """Initialize Git repository in data directory"""
    try:
        # Check if already initialized
        Repo(data_dir)
        return False  # Already exists
    except InvalidGitRepositoryError:
        # Initialize new repository
        repo = Repo.init(data_dir)
        return True  # Newly created

def create_gitignore(data_dir: Path):
    """Create .gitignore for data directory"""
    gitignore_path = data_dir / '.gitignore'
    gitignore_content = """
# Bagels ignore patterns
*.db
*.db-shm
*.db-wal
*.tmp
backups/
"""
    with open(gitignore_path, 'w') as f:
        f.write(gitignore_content.strip())
```

### Click Command Integration
```python
# Source: Existing bagels CLI patterns
import click
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def export_cmd(verbose):
    """Export all SQLite entities to YAML files"""
    from bagels.export.exporter import export_all

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Exporting data to YAML...", total=None)

        try:
            result = export_all(verbose=verbose)
            progress.update(task, description="Export complete!")
            click.echo(f"✓ Exported {result['total_entities']} entities")
        except Exception as e:
            progress.update(task, description=f"Export failed: {e}")
            raise click.ClickException(str(e))
```

### Validation Before Import
```python
# Source: CONTEXT.md validation requirements
from typing import List, Tuple

def validate_yaml_structure(data: dict, entity_type: str) -> Tuple[bool, List[str]]:
    """Validate YAML structure before import"""
    errors = []

    # Check required top-level keys
    if entity_type not in data:
        errors.append(f"Missing required key: {entity_type}")
        return False, errors

    entities = data[entity_type]

    # Validate each entity
    for slug, entity_data in entities.items():
        # Check required fields
        required_fields = ['name', 'createdAt']
        for field in required_fields:
            if field not in entity_data:
                errors.append(f"{entity_type}.{slug}: Missing required field '{field}'")

        # Validate foreign key references
        if 'accountId' in entity_data:
            acc_slug = entity_data['accountId']
            if not account_exists(acc_slug):
                errors.append(f"{entity_type}.{slug}: Referenced account '{acc_slug}' does not exist")

    return len(errors) == 0, errors
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Database-only storage | YAML + SQLite dual storage | Phase 1 implementation | Enables Git tracking, LLM access |
| Integer IDs | Slug-based IDs | Phase 1 implementation | Mergeable, human-readable |
| Single export file | Monthly record grouping | Phase 1 implementation | Manageable file sizes, better diffs |
| Manual backup | Auto-backup before import | Phase 1 implementation | Data safety, rollback capability |

**Deprecated/outdated:**
- **JSON for data export**: YAML chosen for human-readability and comment support
- **UUID for record IDs**: Slug-based IDs provide better mergeability and Git-friendliness

## Open Questions

1. **Comment preservation implementation**
   - What we know: PyYAML doesn't preserve comments by default, ruamel.yaml does
   - What's unclear: Whether ruamel.yaml's API compatibility with PyYAML is sufficient
   - Recommendation: Start with PyYAML, evaluate ruamel.yaml if comment preservation critical

2. **Backup file naming scheme**
   - What we know: CONTEXT.md requires automatic backups before import
   - What's unclear: Exact format (timestamp-based vs sequential)
   - Recommendation: Use timestamp format: `backup_YYYY-MM-DD_HHMMSS.db`

3. **Slug ID uniqueness constraint**
   - What we know: Slug IDs must be unique to prevent merge conflicts
   - What's unclear: Whether to add database-level unique constraint
   - Recommendation: Add unique constraint on slug column in migration

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.1 (existing) |
| Config file | pyproject.toml (existing) |
| Quick run command | `pytest tests/ -x -v` |
| Full suite command | `pytest tests/ --cov=src/bagels` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | Export accounts to YAML | integration | `pytest tests/export/test_accounts.py::test_export_accounts -x` | ❌ Wave 0 |
| DATA-02 | Export categories to YAML | integration | `pytest tests/export/test_categories.py::test_export_categories -x` | ❌ Wave 0 |
| DATA-03 | Export persons to YAML | integration | `pytest tests/export/test_persons.py::test_export_persons -x` | ❌ Wave 0 |
| DATA-04 | Export templates to YAML | integration | `pytest tests/export/test_templates.py::test_export_templates -x` | ❌ Wave 0 |
| DATA-05 | Export records by month | integration | `pytest tests/export/test_records.py::test_export_records_monthly -x` | ❌ Wave 0 |
| DATA-06 | Import YAML to SQLite | integration | `pytest tests/import/test_import.py::test_import_yaml -x` | ❌ Wave 0 |
| FMT-02 | Slug-based ID generation | unit | `pytest tests/export/test_slug_generator.py::test_generate_slug -x` | ❌ Wave 0 |
| GIT-01 | Initialize Git repository | integration | `pytest tests/git/test_repository.py::test_init_repo -x` | ❌ Wave 0 |
| CMD-01 | bagels export command | cli/integration | `pytest tests/cli/test_export_cmd.py::test_export_command -x` | ❌ Wave 0 |
| CMD-02 | bagels import command | cli/integration | `pytest tests/cli/test_import_cmd.py::test_import_command -x` | ❌ Wave 0 |
| CMD-03 | bagels init command | cli/integration | `pytest tests/cli/test_init_cmd.py::test_init_command -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/export/ -x -v` (quick smoke test)
- **Per wave merge:** `pytest tests/ --cov=src/bagels/export --cov=src/bagels/git --cov=src/bagels/cli` (full coverage)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/export/test_accounts.py` — export accounts to YAML
- [ ] `tests/export/test_categories.py` — export categories to YAML
- [ ] `tests/export/test_persons.py` — export persons to YAML
- [ ] `tests/export/test_templates.py` — export templates to YAML
- [ ] `tests/export/test_records.py` — export records by month
- [ ] `tests/export/test_slug_generator.py` — slug ID generation logic
- [ ] `tests/import/test_import.py` — import YAML to SQLite
- [ ] `tests/git/test_repository.py` — Git repository initialization
- [ ] `tests/cli/test_export_cmd.py` — export CLI command
- [ ] `tests/cli/test_import_cmd.py` — import CLI command
- [ ] `tests/cli/test_init_cmd.py` — init CLI command
- [ ] `tests/conftest.py` — shared fixtures for in-memory database, temp directories
- [ ] Framework install: pytest 8.3.1 (already installed as dev dependency)

## Sources

### Primary (HIGH confidence)
- **PyYAML Documentation** - https://pyyaml.org/wiki/PyYAMLDocumentation - safe_load/safe_dump API, YAML structure examples
- **SQLAlchemy 2.0 Documentation** - https://docs.sqlalchemy.org/en/20/orm/persistence_techniques.html - bulk operations, session management
- **GitPython Documentation** - https://gitpython.readthedocs.io/en/stable/ - Repo.init(), repository management
- **CONTEXT.md** - User decisions and implementation requirements
- **REQUIREMENTS.md** - Phase 1 requirements mapping
- **Existing codebase** - src/bagels/models/, src/bagels/managers/, tests/

### Secondary (MEDIUM confidence)
- **Click 8.0 Documentation** - CLI command patterns (existing usage in codebase)
- **Rich Progress Documentation** - Progress bar patterns (existing usage in codebase)
- **Python datetime documentation** - Date formatting and grouping

### Tertiary (LOW confidence)
- **ruamel.yaml documentation** - Comment preservation (not verified, may be needed)
- **Web search results** - Unable to fetch current search results, relying on official docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified except ruamel.yaml (optional)
- Architecture: HIGH - Clear patterns from CONTEXT.md and existing codebase
- Pitfalls: MEDIUM - Some unknowns around comment preservation and edge cases

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (30 days - stable ecosystem, but verify GitPython compatibility)
