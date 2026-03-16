# Phase 2: CLI Query Layer - Research

**Researched:** 2026-03-15
**Domain:** Click-based CLI with Rich tables and SQLAlchemy queries
**Confidence:** HIGH

## Summary

Phase 2 builds a comprehensive CLI query interface on top of the existing Bagels foundation. The project already has Click 8.0, Rich 13.0, and SQLAlchemy 2.0 integrated from Phase 1, providing a solid infrastructure for building table-based query commands with multiple output formats. The key challenge is designing intuitive command structures that balance human-readability with script-friendly JSON output while supporting flexible filtering for dates, categories, and amounts.

**Primary recommendation:** Use Click groups with noun-based commands (`bagels records list`, `bagels categories tree`) rather than verb-noun pairs (`query records`), and implement a shared output formatter module that handles table/JSON/YAML rendering with consistent column ordering and styling.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **Click** | 8.0 | CLI framework | Already integrated, supports groups/subcommands, automatic help generation, elegant flag handling |
| **Rich** | 13.0 | Terminal formatting | Already in use for progress bars, provides Table class with borders/colors/wrapping |
| **SQLAlchemy** | 2.0 | ORM queries | Existing manager layer uses SQLAlchemy 2.0 patterns with joinedload for relationships |
| **PyYAML** | 6.0 | YAML output | Already used in Phase 1 export, proven reliable for structured data |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pytest** | 8.3+ | CLI testing | Use CliRunner from Click testing utilities for command invocation |
| **json** | (stdlib) | JSON output | Use `json.dumps()` with default=str for datetime serialization |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Rich tables | tabulate | Rich already integrated, provides better styling and Unicode box characters |
| Click groups | argparse | Click provides better subcommand composition and automatic help generation |
| SQLAlchemy ORM | Raw SQL | ORM maintains compatibility with existing manager layer, handles relationships automatically |

**Installation:** No additional packages needed - all dependencies already in pyproject.toml from Phase 1.

## Architecture Patterns

### Recommended Project Structure
```
src/bagels/
├── cli/
│   ├── __init__.py
│   ├── records.py          # 'bagels records' command group
│   ├── accounts.py         # 'bagels accounts' command group
│   ├── categories.py       # 'bagels categories' command group
│   ├── spending.py         # 'bagels spending' command group
│   ├── trends.py           # 'bagels trends' command group
│   ├── llm.py              # 'bagels llm context' commands
│   └── utils.py            # Shared output formatting utilities
├── queries/                # NEW: Query layer
│   ├── __init__.py
│   ├── records.py          # Record query builders
│   ├── summaries.py        # Financial summary calculations
│   ├── filters.py          # Common filter patterns (dates, amounts)
│   └── formatters.py       # Output formatters (table/JSON/YAML)
└── managers/               # EXISTING: Business logic layer
    ├── records.py          # Reuse get_records() with filter extensions
    ├── accounts.py         # Reuse existing account queries
    └── categories.py       # Reuse existing category queries
```

### Pattern 1: Click Group with Subcommands
**What:** Organize related commands under noun-based groups
**When to use:** For entity-centric commands (records, accounts, categories)
**Example:**
```python
# Source: https://click.palletsprojects.com/en/8.1.x/commands/#nested-handling-and-contexts
import click

@click.group()
def records():
    """Query and manage records."""
    pass

@records.command("list")
@click.option("--category", "-c", help="Filter by category name")
@click.option("--month", "-m", help="Filter by month (YYYY-MM)")
@click.option("--format", "-f", type=click.Choice(["table", "json", "yaml"]), default="table")
def list_records(category, month, format):
    """List records with optional filters."""
    from bagels.queries.records import query_records
    from bagels.queries.formatters import format_records

    records = query_records(category=category, month=month)
    output = format_records(records, format)
    click.echo(output)
```

### Pattern 2: Shared Output Formatter Module
**What:** Centralize table/JSON/YAML rendering logic
**When to use:** For all query commands to ensure consistent output
**Example:**
```python
# bagels/queries/formatters.py
from rich.table import Table
from rich.console import Console
import json
import yaml
from datetime import datetime

def format_records(records, output_format="table"):
    """Format records list as table, JSON, or YAML."""
    if output_format == "json":
        return json.dumps([_record_to_dict(r) for r in records], default=str, indent=2)
    elif output_format == "yaml":
        return yaml.dump([_record_to_dict(r) for r in records], default_flow_style=False)
    else:  # table
        console = Console()
        table = Table(title="Records")
        table.add_column("ID", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Label", style="white")
        table.add_column("Amount", justify="right", style="yellow")
        table.add_column("Category", style="magenta")

        for record in records:
            table.add_row(
                record.slug or str(record.id),
                record.date.strftime("%Y-%m-%d"),
                record.label,
                f"${record.amount:.2f}",
                record.category.name if record.category else "None"
            )
        return console.render(table)
```

### Pattern 3: SQLAlchemy Query Builder Pattern
**What:** Build queries dynamically based on filter flags
**When to use:** For flexible filtering without complex conditionals
**Example:**
```python
# bagels/queries/records.py
from sqlalchemy.orm import joinedload
from bagels.models.record import Record
from bagels.managers.utils import get_start_end_of_period

def query_records(session, category=None, month=None, amount_range=None):
    """Build and execute record query with optional filters."""
    query = session.query(Record).options(
        joinedload(Record.category),
        joinedload(Record.account)
    )

    # Date filtering
    if month:
        start, end = get_start_end_of_month(month)  # Parse "2026-03"
        query = query.filter(Record.date >= start, Record.date < end)

    # Category filtering
    if category:
        query = query.join(Record.category).filter(Category.name == category)

    # Amount range filtering (e.g., "100..500")
    if amount_range:
        min_amt, max_amt = map(float, amount_range.split(".."))
        query = query.filter(Record.amount.between(min_amt, max_amt))

    return query.order_by(Record.date.desc()).all()
```

### Anti-Patterns to Avoid
- **Don't use verb-noun commands:** `bagels query records` adds unnecessary nesting. Use `bagels records list` instead.
- **Don't hand-roll table formatting:** Rich tables handle borders, wrapping, and alignment. Don't use manual string formatting.
- **Don't mix business logic with CLI code:** Keep queries in `queries/` module, CLI commands only handle parsing and output.
- **Don't use datetime strings directly:** Always parse user input to datetime objects before SQLAlchemy queries.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Table formatting | Manual string padding and borders | Rich Table class | Handles Unicode box characters, column wrapping, alignment, colors automatically |
| JSON serialization | Custom datetime converters | `json.dumps(data, default=str)` | Built-in datetime serialization handles all SQLAlchemy types |
| CLI argument parsing | Manual sys.argv parsing | Click decorators | Handles types, defaults, help text, validation automatically |
| Date range calculations | Manual month arithmetic | `get_start_end_of_month()` from utils | Already handles month boundaries and leap years correctly |
| Output format detection | if/elif chains for format flags | Click Choice type + format functions | Click validates choices, prevents invalid formats |

**Key insight:** The project already has Rich and Click integrated. Resist the temptation to build custom formatting utilities - the existing libraries handle edge cases like terminal width detection, Unicode rendering, and argument validation.

## Common Pitfalls

### Pitfall 1: Session Management in CLI Commands
**What goes wrong:** Database sessions are created but never closed, causing connection leaks.
**Why it happens:** CLI commands exit early on errors or user interruptions, skipping cleanup code.
**How to avoid:** Use try/finally blocks or context managers for session lifecycle:
```python
def list_records():
    session = Session()
    try:
        records = session.query(Record).all()
        # ... format and output
    finally:
        session.close()
```

### Pitfall 2: Naive DateTime String Comparisons
**What goes wrong:** Queries like `Record.date >= "2026-03-01"` fail because SQLAlchemy expects datetime objects.
**Why it happens:** Click returns strings from user input, developers forget to parse to datetime.
**How to avoid:** Always parse date strings immediately after Click validation:
```python
@click.option("--month", callback=validate_month_format)
def list_records(month):
    # callback ensures month is datetime or None
```

### Pitfall 3: Rich Table Terminal Width Issues
**What goes wrong:** Tables render incorrectly on narrow terminals, content wraps ugly or gets truncated.
**Why it happens:** Rich calculates column widths based on content, not terminal size.
**How to avoid:** Use `max_width` on columns and `expand=False` on table:
```python
table = Table(expand=False)
table.add_column("Label", max_width=30)  # Truncate long labels
```

### Pitfall 4: Inconsistent JSON Serialization
**What goes wrong:** Some commands return datetime objects in JSON, causing serialization errors.
**Why it happens:** Developers forget `default=str` in `json.dumps()` for datetime/Decimal types.
**How to avoid:** Create a shared JSON encoder function:
```python
def to_json(data):
    return json.dumps(data, default=str, indent=2)
```

### Warning Signs
- CLI commands hang or timeout → Likely session leak
- "Object of type datetime is not JSON serializable" → Missing default=str
- Tables overflow terminal width → Need max_width on columns
--help shows duplicate options → Click decorator order wrong

## Code Examples

Verified patterns from official sources:

### Click Group with Subcommands
```python
# Source: https://click.palletsprojects.com/en/8.1.x/commands/#nested-handling-and-contexts
import click

@click.group()
def cli():
    """Main entry point."""
    pass

@cli.group()
def records():
    """Record management commands."""
    pass

@records.command("list")
@click.option("--category", help="Filter by category")
def list_records(category):
    """List all records."""
    click.echo(f"Listing records for category: {category}")

# Usage: bagels records list --category Groceries
```

### Rich Table with Styling
```python
# Source: https://rich.readthedocs.io/en/stable/tables.html
from rich.table import Table
from rich.console import Console

table = Table(title="Records", show_header=True, header_style="bold magenta")
table.add_column("ID", style="cyan", width=6)
table.add_column("Label", style="white")
table.add_column("Amount", justify="right", style="green")

table.add_row("1", "Groceries", "150.00")
table.add_row("2", "Gas", "45.00")

console = Console()
console.print(table)
```

### SQLAlchemy Filtering with Relationships
```python
# Source: Existing codebase pattern (managers/records.py lines 82-108)
from sqlalchemy.orm import joinedload

query = session.query(Record).options(
    joinedload(Record.category),
    joinedload(Record.account)
)

# Date range filter
start, end = get_start_end_of_month(offset=0)
query = query.filter(Record.date >= start, Record.date < end)

# Category filter
query = query.join(Record.category).filter(Category.name == "Groceries")

# Amount filter with operator
query = query.filter(Record.amount.op(">")(100))

records = query.all()
```

### Click Choice for Output Format
```python
# Source: https://click.palletsprojects.com/en/8.1.x/options/#choice-options
import click

@click.command()
@click.option(
    "--format", "-f",
    type=click.Choice(["table", "json", "yaml"], case_sensitive=False),
    default="table"
)
def show_data(format):
    """Show data in specified format."""
    if format == "json":
        click.echo(json.dumps(data))
    elif format == "yaml":
        click.echo(yaml.dump(data))
    else:
        render_table(data)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| argparse + manual parsing | Click decorators | Click 8.0 (current) | Automatic help generation, type validation, cleaner code |
| ASCII table borders | Rich Unicode box characters | Rich 13.0 (current) | Beautiful tables with double-lines, rounded corners |
| Raw SQL queries | SQLAlchemy 2.0 ORM | SQLAlchemy 2.0 (current) | Type-safe queries, relationship loading, cross-database compatibility |
| Custom datetime handling | Click parameter types + validators | Click 8.0 | Built-in date parsing, validation error messages |

**Deprecated/outdated:**
- **optparse/argparse:** Replaced by Click in modern Python CLIs
- **prettytable/tabulate:** Rich tables provide superior styling and are already integrated
- **SQLAlchemy 1.x session.execute():** SQLAlchemy 2.0 uses session.query() or select() constructs

## Open Questions

1. **Should we support complex query languages (e.g., `--query 'category==Food and amount>100'`)?**
   - What we know: Click can parse custom types, but parsing query strings adds complexity
   - What's unclear: User need for ad-hoc queries vs. pre-built filter flags
   - Recommendation: Start with flag-based filters (`--category`, `--amount`), add query language in v2 if users request it

2. **How to handle large datasets in table output?**
   - What we know: Rich handles table wrapping but 1000+ rows will be unusable
   - What's unclear: Typical record count per user, need for pagination
   - Recommendation: Implement `--limit` flag defaulting to 50, add `--all` flag for full output

3. **Should JSON output include nested relationships or just IDs?**
   - What we know: LLM context needs full nested data (category.name, account.name)
   - What's unclear: Performance impact of eager loading all relationships
   - Recommendation: Use `joinedload()` for all queries, JSON includes nested objects by default

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ |
| Config file | pyproject.toml (tool.pytest.ini_options) |
| Quick run command | `pytest tests/cli/test_records.py -x -v` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CLI-01 | `bagels records list --month` table output | integration | `pytest tests/cli/test_records.py::test_records_list_month -x` | ❌ Wave 0 |
| CLI-02 | `bagels records list --category --date-from --date-to` filtering | integration | `pytest tests/cli/test_records.py::test_records_filter_category -x` | ❌ Wave 0 |
| CLI-03 | `bagels summary --month` financial overview | integration | `pytest tests/cli/test_summary.py::test_summary_month -x` | ❌ Wave 0 |
| CLI-04 | `bagels accounts list --format yaml` | integration | `pytest tests/cli/test_accounts.py::test_accounts_yaml -x` | ❌ Wave 0 |
| CLI-05 | `bagels categories tree` hierarchical display | integration | `pytest tests/cli/test_categories.py::test_categories_tree -x` | ❌ Wave 0 |
| CLI-06 | `bagels spending --by-category --month` | integration | `pytest tests/cli/test_spending.py::test_spending_by_category -x` | ❌ Wave 0 |
| CLI-07 | `bagels spending --by-day --month` daily breakdown | integration | `pytest tests/cli/test_spending.py::test_spending_by_day -x` | ❌ Wave 0 |
| CLI-08 | `bagels trends --months` comparison | integration | `pytest tests/cli/test_trends.py::test_trends_months -x` | ❌ Wave 0 |
| CLI-09 | JSON output for all query commands | integration | `pytest tests/cli/test_output_formats.py::test_json_format -x` | ❌ Wave 0 |
| CLI-10 | `bagels add record --from-yaml` batch import | integration | `pytest tests/cli/test_import.py::test_add_from_yaml -x` | ❌ Wave 0 |
| LLM-01 | `bagels llm context --month` snapshot | integration | `pytest tests/cli/test_llm.py::test_llm_context_month -x` | ❌ Wave 0 |
| LLM-02 | `bagels schema` full schema | integration | `pytest tests/cli/test_schema.py::test_schema_full -x` | ❌ Wave 0 |
| LLM-03 | `bagels schema records` model schema | integration | `pytest tests/cli/test_schema.py::test_schema_model -x` | ❌ Wave 0 |
| LLM-04 | Context includes all required entities | integration | `pytest tests/cli/test_llm.py::test_context_completeness -x` | ❌ Wave 0 |
| LLM-05 | Context includes budget status | integration | `pytest tests/cli/test_llm.py::test_context_budget_status -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/cli/ -x -v` (quick feedback on CLI tests)
- **Per wave merge:** `pytest tests/ -v` (full test suite including existing tests)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/cli/test_records.py` — CLI-01, CLI-02, CLI-09
- [ ] `tests/cli/test_summary.py` — CLI-03
- [ ] `tests/cli/test_accounts.py` — CLI-04
- [ ] `tests/cli/test_categories.py` — CLI-05
- [ ] `tests/cli/test_spending.py` — CLI-06, CLI-07
- [ ] `tests/cli/test_trends.py` — CLI-08
- [ ] `tests/cli/test_import.py` — CLI-10
- [ ] `tests/cli/test_llm.py` — LLM-01, LLM-04, LLM-05
- [ ] `tests/cli/test_schema.py` — LLM-02, LLM-03
- [ ] `tests/cli/test_output_formats.py` — CLI-09
- [ ] `tests/cli/conftest.py` — Shared CLI test fixtures (CliRunner, sample data)

*(None of the CLI-specific test files exist yet - Wave 0 task to create test file structure)*

## Sources

### Primary (HIGH confidence)
- Click 8.1.x Documentation - https://click.palletsprojects.com/en/8.1.x/ (verified command groups, options, Choice type)
- Rich 14.1.0 Documentation - https://rich.readthedocs.io/en/stable/tables.html (verified Table API, column options, border styles)
- Existing codebase - `src/bagels/__main__.py` (verified Click integration pattern)
- Existing codebase - `src/bagels/cli/export.py` (verified CLI command pattern with Rich progress)
- Existing codebase - `src/bagels/managers/records.py` (verified SQLAlchemy query patterns with joinedload)
- Existing codebase - `tests/conftest.py` (verified pytest fixtures and in_memory_db pattern)

### Secondary (MEDIUM confidence)
- SQLAlchemy 2.0 Documentation - Query filtering with between() and join() patterns (verified against existing codebase usage)
- pytest CLI testing - Click's CliRunner for testing CLI commands (standard pattern for Click CLIs)

### Tertiary (LOW confidence)
- None - all findings verified against official docs or existing codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already integrated, versions verified in pyproject.toml
- Architecture: HIGH - Patterns verified against existing codebase (managers, CLI structure)
- Pitfalls: HIGH - Based on common Click/SQLAlchemy issues, verified against existing session management patterns
- Test infrastructure: HIGH - pytest 8.3+ already configured, conftest.py fixtures available

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (30 days - stable CLI library ecosystem, but verify if new Click/Rich versions released)
