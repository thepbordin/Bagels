---
phase: 02-cli-query-layer
plan: 02a
type: execute
wave: 1
depends_on: []
files_modified:
  - src/bagels/cli/records.py
  - src/bagels/__main__.py
  - tests/cli/test_records.py
autonomous: true
requirements:
  - CLI-01
  - CLI-02
  - CLI-03
must_haves:
  truths:
    - User can run `bagels records list` to see all records in table format
    - User can filter records by month with --month flag
    - User can filter records by category with --category flag
    - User can filter records by date range with --date-from and --date-to flags
    - User can filter records by amount range with --amount flag
    - User can view a single record with `bagels records show <id>`
  artifacts:
    - path: src/bagels/cli/records.py
      provides: Click command group for record queries
      exports: ["records", "list_records", "show_record"]
      min_lines: 150
    - path: tests/cli/test_records.py
      provides: Integration tests for records query commands
      exports: ["test_records_list_default", "test_records_list_month", "test_records_filter_category", "test_records_show_valid"]
      min_lines: 120
  key_links:
    - from: src/bagels/cli/records.py
      to: src/bagels/queries/formatters.py
      via: import statement
      pattern: "from bagels.queries.formatters import format_records"
    - from: src/bagels/cli/records.py
      to: src/bagels/queries/filters.py
      via: import statement
      pattern: "from bagels.queries.filters import"
    - from: src/bagels/__main__.py
      to: src/bagels/cli/records.py
      via: cli.add_command()
      pattern: "cli.add_command(records, name='records')"
---

<objective>
Implement records query commands (list and show) with comprehensive filtering capabilities, enabling users to search and view financial records.

Purpose: Provide the primary interface for querying financial records with flexible filtering by month, category, date range, amount, account, and person. This is the most frequently used query command and serves as the pattern for other query commands.

Output: Working `bagels records` command group with list and show subcommands.
</objective>

<execution_context>
@/Users/thepbordin/.claude/get-shit-done/workflows/execute-plan.md
@/Users/thepbordin/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/02-cli-query-layer/02-CONTEXT.md
@.planning/phases/02-cli-query-layer/02-RESEARCH.md

# Shared infrastructure (from Plan 02-01)
@.planning/phases/02-cli-query-layer/02-01-PLAN.md

# Existing codebase patterns
@src/bagels/__main__.py
@src/bagels/managers/records.py
@src/bagels/cli/export.py
</context>

<interfaces>
<!-- From Plan 02-01 (shared infrastructure) -->
From src/bagels/queries/formatters.py:
```python
def format_records(records: list[Record], output_format: str = "table") -> str
def to_json(data: list | dict) -> str
def to_yaml(data: list | dict) -> str
```

From src/bagels/queries/filters.py:
```python
def parse_month(month_str: str | None) -> tuple[datetime, datetime] | None
def parse_amount_range(range_str: str | None) -> tuple[float, float] | None
def apply_date_filters(query, month: str | None, date_from: str | None, date_to: str | None) -> Query
def apply_category_filter(query, category_name: str | None) -> Query
def apply_amount_filter(query, amount_range: str | None) -> Query
```

<!-- From existing codebase -->
From src/bagels/managers/records.py:
```python
def get_records(
    session,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    category: str | None = None,
    account: str | None = None
) -> list[Record]
```
</interfaces>

<tasks>

<task type="auto">
  <name>Task 1: Create records command group</name>
  <files>src/bagels/cli/records.py</files>
  <action>
Create Click command group for record queries:

1. **Command group structure**:
   ```python
   @click.group()
   def records():
       """Query and manage records."""
       pass
   ```

2. **list subcommand** (implements CLI-01, CLI-02):
   ```python
   @records.command("list")
   @click.option("--category", "-c", help="Filter by category name")
   @click.option("--month", "-m", help="Filter by month (YYYY-MM)")
   @click.option("--date-from", help="Start date (YYYY-MM-DD)")
   @click.option("--date-to", help="End date (YYYY-MM-DD)")
   @click.option("--amount", help="Amount range (e.g., 100..500)")
   @click.option("--account", "-a", help="Filter by account name")
   @click.option("--person", "-p", help="Filter by person name")
   @click.option("--format", "-f", type=click.Choice(["table", "json", "yaml"]), default="table")
   @click.option("--limit", type=int, default=50, help="Maximum records to display")
   @click.option("--all", is_flag=True, help="Show all records (no limit)")
   def list_records(category, month, date_from, date_to, amount, account, person, format, limit, all):
       """List records with optional filters."""
   ```

3. **show subcommand** (implements CLI-03):
   ```python
   @records.command("show")
   @click.argument("record_id", type=str)
   @click.option("--format", "-f", type=click.Choice(["table", "json", "yaml"]), default="table")
   def show_record(record_id, format):
       """Show details for a single record."""
   ```

Follow Click group pattern from Phase 1 (src/bagels/cli/export.py).
  </action>
  <verify>
python -c "from bagels.cli.records import records; print(records.name)"
  </verify>
  <done>Records command group created with list and show subcommands</done>
</task>

<task type="auto">
  <name>Task 2: Implement records list command</name>
  <files>src/bagels/cli/records.py</files>
  <action>
Implement list_records command logic:

1. **Session management**:
   - Create SQLAlchemy session using get_session()
   - Use try/finally block to ensure session cleanup

2. **Build query**:
   - Start with session.query(Record).options(joinedload(Record.category), joinedload(Record.account))
   - Apply filters using filter utilities from 02-01:
     * apply_date_filters() for month, date_from, date_to
     * apply_category_filter() for category
     * apply_amount_filter() for amount
   - Filter by account name if provided
   - Filter by person name if provided
   - Apply limit unless --all flag is set
   - Order by Record.date.desc()

3. **Execute and format**:
   - Execute query with .all()
   - Pass records to format_records() from formatters.py
   - Echo output to terminal

4. **Error handling**:
   - Catch ValueError from filter parsing (invalid month format, bad amount range)
   - Display user-friendly error messages via ClickException
   - Handle "no records found" gracefully with informative message

5. **Limit handling**:
   - Default limit: 50 records
   - If --all flag: no limit applied
   - Show warning if query returns limit results (may be more)

Reuse get_records() pattern from managers/records.py as reference.
  </action>
  <verify>
pytest tests/cli/test_records.py::test_records_list_default -x
pytest tests/cli/test_records.py::test_records_list_month -x
pytest tests/cli/test_records.py::test_records_filter_category -x
  </verify>
  <done>Records list command filters and displays records correctly</done>
</task>

<task type="auto">
  <name>Task 3: Implement records show command</name>
  <files>src/bagels/cli/records.py</files>
  <action>
Implement show_record command logic:

1. **Record lookup**:
   - Query Record by slug or integer ID
   - Use joinedload for category, account, person relationships
   - Handle case where record not found (404 error)

2. **Display formatting**:
   - If format="table": Use Rich table with all record fields
   - If format="json": Use to_json() with _record_to_dict()
   - If format="yaml": Use to_yaml() with _record_to_dict()

3. **Show related splits**:
   - Query splits associated with the record
   - Display in table format below record details

4. **Error handling**:
   - Record not found: Display "Record not found" error
   - Invalid format: Click validates choice, no handling needed

Use format_records() or create single-record formatter.
  </action>
  <verify>
pytest tests/cli/test_records.py::test_records_show_valid -x
pytest tests/cli/test_records.py::test_records_show_not_found -x
  </verify>
  <done>Records show command displays single record with all details</done>
</task>

<task type="auto">
  <name>Task 4: Register records command and create tests</name>
  <files>src/bagels/__main__.py, tests/cli/test_records.py</files>
  <action>
Part A: Register records command group in main CLI:

1. **Import records group**:
   ```python
   from bagels.cli.records import records
   ```

2. **Add to CLI**:
   ```python
   cli.add_command(records, name="records")
   ```

3. **Verify help text**:
   - `bagels --help` should show "records" command
   - `bagels records --help` should show list and show subcommands

Part B: Create comprehensive integration tests for records commands:

1. **List command tests** (CLI-01, CLI-02):
   - test_records_list_default: Verify table output with no filters
   - test_records_list_month: Verify --month flag filters correctly
   - test_records_list_date_range: Verify --date-from and --date-to
   - test_records_filter_category: Verify --category flag
   - test_records_filter_amount: Verify --amount range parsing
   - test_records_filter_account: Verify --account flag
   - test_records_format_json: Verify JSON output
   - test_records_format_yaml: Verify YAML output
   - test_records_limit_default: Verify 50 record default limit
   - test_records_limit_all: Verify --all flag removes limit

2. **Show command tests** (CLI-03):
   - test_records_show_valid: Verify showing existing record by slug
   - test_records_show_not_found: Verify error on invalid ID
   - test_records_show_json: Verify JSON format output

Update placeholder tests from Plan 00-00 with full implementations.

Follow existing command registration pattern. Use CliRunner for integration tests. Use sample_db_with_records fixture.
  </action>
  <verify>
bagels --help | grep records
bagels records --help | grep "Query and manage records"
pytest tests/cli/test_records.py -x (all tests pass)
  </verify>
  <done>Records command group accessible via CLI with full test coverage</done>
</task>

</tasks>

<verification>
1. pytest tests/cli/test_records.py -x passes (all records command tests)
2. `bagels records list` displays records in table format
3. `bagels records list --month 2026-03` filters by month correctly
4. `bagels records list --category Food` filters by category
5. `bagels records show r_2026-03-14_001` displays single record
6. All filter flags work correctly (date range, amount, account, person)
</verification>

<success_criteria>
1. Records command group registered in CLI
2. List command supports all filters (month, category, date range, amount, account, person)
3. Show command displays single record with details
4. Both commands support table/JSON/YAML output formats
5. Test coverage for all commands and filter combinations
</success_criteria>

<output>
After completion, create `.planning/phases/02-cli-query-layer/02-02a-SUMMARY.md`
</output>
