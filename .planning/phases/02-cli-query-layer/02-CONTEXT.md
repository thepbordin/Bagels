# Phase 2: CLI Query Layer - Context

**Gathered:** 2026-03-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Provide comprehensive CLI interface for querying records, summaries, and LLM context dumps. Users can query financial data through structured text commands with multiple output formats (table, JSON, YAML). LLM integration includes schema commands and context dumps for AI-powered financial analysis.

</domain>

<decisions>
## Implementation Decisions

### Command Structure
- **Top-level commands** without 'query' prefix: `bagels records`, `bagels summary`, `bagels accounts`, `bagels spending`, `bagels trends`
- **Noun-based subcommands**: `bagels records list`, `bagels records show <id>`, `bagels categories tree`
- **Separate groups** for LLM and schema: `bagels llm context`, `bagels db schema`
- **Flat structure**: No nested command groups like `query:records`, all commands at same level for discoverability

### LLM Context Format
- **Structured YAML** output for reliable LLM parsing: `accounts: [{name: Savings, balance: 5000}, ...]`
- **Full financial snapshot** by default: all accounts, recent records (current month), categories, budget status, spending trends
- **Current month** for recent records (aligns with budget cycle)
- **Customizable time range** via flags: `--period all`, `--days 60`, `--month 2026-03`
- **All models in YAML** for `bagels schema` command: complete schema for Record, Account, Category, Person, Template

### Output Format Defaults
- **Table format by default** (human-first design): `bagels records list` → Rich table
- **All columns shown** by default: use `--output/-o col1,col2` to select specific columns
- **Flat array for JSON**: `[{id: r_001, amount: 50, label: Groceries}, ...]` - simple, script-friendly
- **Both individual and short flags**: `--table/-t`, `--json/-j`, `--yaml/-y` available for all commands

### Filtering and Flag Design
- **Flag-based filters**: `bagels records list --category Food --amount 100..500 --month 2026-03`
- **Both long and short** for common filters: `--category/-c`, `--account/-a`, `--person/-p`, `--month/-m`
- **Specific date flags**: `--month 2026-03`, `--date-from 2026-03-01`, `--date-to 2026-03-31`
- **Range syntax** for amounts: `--amount 100..500` (inclusive range), `--amount-gt 100`, `--amount-lt 500` also supported

### Claude's Discretion
- Exact table column ordering and width defaults
- Rich table styling options (borders, colors, alignment)
- Error message format for invalid filter combinations
- Progress indicators for long-running queries
- Whether to support complex query language (e.g., `--query 'category==Food and amount>100'`)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Click 8.0 CLI framework** — Already used for main `bagels` command in `src/bagels/__main__.py`, supports groups, subcommands, and flags
- **Rich table library** — Already used for progress bars, provides table rendering with borders, colors, and alignment
- **Manager classes** — Business logic in `src/bagels/managers/` (accounts.py, categories.py, persons.py, records.py, record_templates.py, splits.py, utils.py)
- **SQLAlchemy 2.0 ORM** — Models with relationships, can query with filters via SQLAlchemy expressions
- **YAML 6.0 library** — Already available from Phase 1, can be reused for schema and context output

### Established Patterns
- **CLI command groups** — Phase 1 created `src/bagels/cli/` with export.py, import.py, init.py commands
- **Manager methods** — Each manager has list/show/create/update/delete methods for data access
- **Pydantic validation** — Used in Phase 1 for schema validation, can be reused for query validation
- **Session management** — SQLAlchemy session pattern already established, can be reused for queries
- **Absolute imports** — All imports use absolute paths from project root (e.g., `from bagels.models.account import Account`)

### Integration Points
- **CLI entry point** — `src/bagels/__main__.py` contains Click CLI group, add new top-level commands here
- **Database queries** — Manager classes in `src/bagels/managers/` provide data access layer
- **Model layer** — Query commands read from SQLAlchemy models directly, no new data structures needed
- **Output formatting** — Rich tables for human output, YAML/JSON serialization via existing libraries

</code_context>

<specifics>
## Specific Ideas

- Table-first design: "I want to run `bagels records list` and see a readable table immediately, flags for power users"
- Range syntax for amounts: "Like how some tools accept `100..500`, that's intuitive for ranges"
- Current month default for LLM context: "Aligns with budget cycle, most questions are about 'this month'"
- Structured YAML for LLM: "LLMs parse YAML reliably, lets the AI reason about the data structure"
- Flag-based filters: "Click-style flags are familiar, `--category Food` is clearer than positional args"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-cli-query-layer*
*Context gathered: 2026-03-15*
