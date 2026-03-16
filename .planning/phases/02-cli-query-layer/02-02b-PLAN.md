---
phase: 02-cli-query-layer
plan: 02b
type: execute
wave: 1
depends_on: []
files_modified:
  - src/bagels/cli/records.py
  - tests/cli/test_records.py
autonomous: true
requirements:
  - CLI-10
must_haves:
  truths:
    - User can batch import records from YAML with `bagels records add --from-yaml`
    - Validation errors display before importing
    - Foreign keys (accountSlug, categorySlug, personSlug) resolve correctly
    - Progress feedback shows during import
    - Import count displays after completion
  artifacts:
    - path: src/bagels/cli/records.py
      provides: Batch import functionality for records
      exports: ["add_record"]
      min_lines: 80 (additional to 02-02a)
    - path: tests/cli/test_records.py
      provides: Integration tests for batch import
      exports: ["test_add_from_yaml", "test_add_from_yaml_validation", "test_add_from_yaml_foreign_keys"]
      min_lines: 60 (additional to 02-02a)
  key_links:
    - from: src/bagels/cli/records.py
      to: src/bagels/managers/records.py
      via: import statement
      pattern: "from bagels.managers.records import"
    - from: tests/cli/test_records.py
      to: src/bagels/cli/records.py
      via: CliRunner invocation
      pattern: "runner.invoke(records, ['add', '--from-yaml'])"
---

<objective>
Implement batch import functionality for records from YAML files, enabling users to quickly add multiple records at once.

Purpose: Provide efficient bulk data entry for records via YAML files. This is useful for migrating data from other systems, entering historical data, or rapid prototyping. The command validates data before import and provides progress feedback for large batches.

Output: Working `bagels records add --from-yaml` command with validation and progress feedback.
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

# Records command group (from Plan 02-02a)
@.planning/phases/02-cli-query-layer/02-02a-PLAN.md

# Existing codebase patterns
@src/bagels/cli/import.py
@src/bagels/managers/records.py
</context>

<interfaces>
<!-- From existing codebase -->
From src/bagels/managers/records.py:
```python
def create_record(session, record_data: dict) -> Record
```

From Phase 1 import pattern (src/bagels/cli/import.py):
```python
# YAML file loading and validation patterns
import yaml
from pathlib import Path
```
</interfaces>

<tasks>

<task type="auto">
  <name>Task 1: Implement batch import from YAML</name>
  <files>src/bagels/cli/records.py</files>
  <action>
Implement add_record command with --from-yaml flag:

1. **Add subcommand to records group** (implements CLI-10):
   ```python
   @records.command("add")
   @click.option("--from-yaml", type=click.Path(exists=True), help="Import records from YAML file")
   def add_record(from_yaml):
       """Add records (batch import from YAML)."""
   ```

2. **YAML file parsing**:
   - Load YAML file using yaml.safe_load()
   - Validate structure (list of record dicts or dict with records key)
   - Accept both formats:
     * List: `[{label: Groceries, amount: 50, ...}, ...]`
     * Dict with records key: `{records: [{label: Groceries, ...}, ...]}`

3. **Validation**:
   - Validate each record has required fields: label, amount, date
   - Validate date format (YYYY-MM-DD)
   - Validate foreign keys exist (accountSlug, categorySlug, personSlug)
   - Display validation errors before importing
   - Show count of valid vs invalid records

4. **Import logic**:
   - Create Record objects from YAML data
   - Resolve foreign keys (accountSlug → accountId, categorySlug → categoryId, personSlug → personId)
   - Generate slug for new records using existing pattern
   - Add to session and commit in batches (commit every 100 records for large files)

5. **Progress feedback**:
   - Show progress bar for batch imports using Rich Progress
   - Display count of imported records
   - Show validation errors if any
   - Display success message with total count

Reuse import logic from Phase 1 (src/bagels/cli/import.py) as reference.
  </action>
  <verify>
pytest tests/cli/test_records.py::test_add_from_yaml -x
pytest tests/cli/test_records.py::test_add_from_yaml_validation -x
  </verify>
  <done>Batch import from YAML works with validation and progress feedback</done>
</task>

<task type="auto">
  <name>Task 2: Create integration tests for batch import</name>
  <files>tests/cli/test_records.py</files>
  <action>
Create comprehensive integration tests for batch import:

1. **Basic import tests** (CLI-10):
   - test_add_from_yaml: Verify batch import from valid YAML file
   - test_add_from_yaml_multiple: Verify importing multiple records
   - test_add_from_yaml_empty: Verify handles empty YAML gracefully

2. **Validation tests**:
   - test_add_from_yaml_validation: Verify validation errors display
   - test_add_from_yaml_missing_fields: Verify missing required fields caught
   - test_add_from_yaml_invalid_date: Verify invalid date format caught
   - test_add_from_yaml_partial_failure: Verify valid records import even if some fail

3. **Foreign key tests**:
   - test_add_from_yaml_foreign_keys: Verify FK resolution (accountSlug, categorySlug, personSlug)
   - test_add_from_yaml_invalid_fk: Verify error on non-existent foreign keys
   - test_add_from_yaml_create_categories: Verify categories can be created inline

4. **Format support tests**:
   - test_add_from_yaml_list_format: Verify list format YAML works
   - test_add_from_yaml_dict_format: Verify dict with records key works

Use CliRunner for integration tests. Create temporary YAML files using tmp_path fixture. Use sample_db_with_records fixture for existing data.
  </action>
  <verify>
pytest tests/cli/test_records.py -x (all tests pass including new import tests)
  </verify>
  <done>CLI-10 requirement met with comprehensive test coverage</done>
</task>

</tasks>

<verification>
1. pytest tests/cli/test_records.py -x passes (all records command tests including import)
2. `bagels records add --from-yaml data.yaml` imports records successfully
3. Validation errors display before import for invalid data
4. Foreign keys resolve correctly (accountSlug → account, categorySlug → category)
5. Progress bar shows during import for large files
6. Success message displays with count of imported records
</verification>

<success_criteria>
1. Add command imports records from YAML file
2. Validation catches missing fields, invalid dates, non-existent foreign keys
3. Progress feedback displays during import
4. Foreign keys resolve correctly
5. Test coverage for all validation scenarios
6. Works with Plan 02-02a records command group
</success_criteria>

<output>
After completion, create `.planning/phases/02-cli-query-layer/02-02b-SUMMARY.md`
</output>
