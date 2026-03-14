---
phase: 01-foundation
plan: 01b
type: execute
wave: 1
depends_on: ["01-01"]
files_modified: [tests/export/test_records.py, tests/export/test_slug_generator.py]
autonomous: true
requirements: [DATA-05, FMT-02, FMT-03]
must_haves:
  truths:
    - Tests can verify record export with monthly grouping
    - Tests can verify slug-based ID generation
    - Tests can verify date-based slug sequencing
  artifacts:
    - path: "tests/export/test_records.py"
      provides: "Record export with monthly grouping tests"
      min_lines: 40
    - path: "tests/export/test_slug_generator.py"
      provides: "Slug-based ID generation logic tests"
      min_lines: 50
  key_links:
    - from: "tests/export/test_records.py"
      to: "conftest.py"
      via: "pytest fixtures"
      pattern: "@pytest.fixture"
    - from: "tests/export/test_slug_generator.py"
      to: "conftest.py"
      via: "pytest fixtures"
      pattern: "@pytest.fixture"
---

<objective>
Create record export tests with monthly grouping and slug generator unit tests using TDD approach. These tests define expected behavior for the most complex export scenarios: date-based record grouping and mergeable slug ID generation.

Purpose: Test-Driven Development for record export ensures monthly grouping works correctly and slug generation supports merge-by-ID strategy. Slug generation is critical for multi-device workflows.
Output: Two test files (records, slug generator) with failing tests (RED phase of TDD).
</objective>

<execution_context>
@/Users/thepbordin/.claude/get-shit-done/workflows/execute-plan.md
@/Users/thepbordin/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/01-foundation/01-CONTEXT.md
@.planning/phases/01-foundation/01-RESEARCH.md
@.planning/phases/01-foundation/01-01-SUMMARY.md
@tests/conftest.py
@src/bagels/models/record.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create record export tests with monthly grouping (TDD - RED)</name>
  <files>tests/export/test_records.py</files>
  <action>
Create tests for record export with monthly grouping:

**Test 1: Export records for single month**
- Given: 5 records all in March 2026
- When: export_records_by_month(session, temp_dir)
- Then: File created at temp_dir/records/2026-03.yaml
- And: YAML contains all 5 records
- And: Records keyed by slug (r_2026-03-14_001 format)

**Test 2: Export records across multiple months**
- Given: 10 records across Jan, Feb, Mar 2026
- When: export_records_by_month(session, temp_dir)
- Then: 3 files created: 2026-01.yaml, 2026-02.yaml, 2026-03.yaml
- And: Each file contains only records for that month
- And: No records in wrong month file

**Test 3: Slug-based ID generation**
- Given: 3 records on same date (2026-03-14)
- When: Exported to YAML
- Then: Slugs are r_2026-03-14_001, r_2026-03-14_002, r_2026-03-14_003
- And: Sequence numbers increment correctly

**Test 4: Export includes all record fields**
- Given: Record with label, amount, date, accountId, categoryId, personId, isIncome, isTransfer
- When: Exported to YAML
- Then: All fields present
- And: Foreign keys use slug references
- And: Timestamps in ISO format
- And: Amount is float with proper precision (2 decimals)

**Test 5: Export handles empty months**
- Given: No records in database
- When: export_records_by_month(session, temp_dir)
- Then: No files created (or empty directory)
- And: No errors thrown

Test slug generation logic thoroughly - this is critical for mergeability (FMT-02).
  </action>
  <verify>
pytest tests/export/test_records.py -x -v  # Should fail (RED phase)
  </verify>
  <done>
- test_records.py created with 5+ test cases
- Tests fail (expected - RED phase)
- Tests cover DATA-05, FMT-02, FMT-03 requirements
- Slug generation logic thoroughly tested
  </done>
</task>

<task type="auto">
  <name>Task 2: Create slug generator unit tests (TDD - RED)</name>
  <files>tests/export/test_slug_generator.py</files>
  <action>
Create unit tests for slug-based ID generation logic:

**Test 1: Generate first slug of day**
- Given: No existing records for date 2026-03-14
- When: generate_record_slug(date(2026, 3, 14), session)
- Then: Returns "r_2026-03-14_001"

**Test 2: Generate sequential slugs for same day**
- Given: 2 existing records with slugs r_2026-03-14_001, r_2026-03-14_002
- When: generate_record_slug(date(2026, 3, 14), session)
- Then: Returns "r_2026-03-14_003"

**Test 3: Generate slug for different day**
- Given: Records exist for 2026-03-14
- When: generate_record_slug(date(2026, 03, 15), session)
- Then: Returns "r_2026-03-15_001" (resets sequence)

**Test 4: Handle gaps in sequence**
- Given: Only r_2026-03-14_001 and r_2026-03-14_005 exist
- When: generate_record_slug(date(2026, 3, 14), session)
- Then: Returns "r_2026-03-14_006" (fills next, not gap)

**Test 5: Handle records without slugs**
- Given: Old records with no slug field
- When: generate_record_slug(date, session)
- Then: Ignores records without slugs
- And: Returns correct next sequence

**Test 6: Validate slug format**
- Given: Generated slug
- When: Checked with regex
- Then: Matches pattern r_YYYY-MM-DD_###

Slug generation is the mergeability secret sauce - test edge cases thoroughly.
  </action>
  <verify>
pytest tests/export/test_slug_generator.py -x -v  # Should fail (RED phase)
  </verify>
  <done>
- test_slug_generator.py created with 6+ test cases
- Tests fail (expected - RED phase)
- Tests cover FMT-02 requirement with edge cases
- Slug format validation included
  </done>
</task>

</tasks>

<verification>
After completing all tasks:

1. **Test Discovery**: Verify all tests are discoverable by pytest
   ```bash
   pytest tests/export/test_records.py tests/export/test_slug_generator.py --collect-only
   ```
   Expected: 11+ tests collected across 2 test files

2. **Red Phase Confirmation**: Verify all tests fail (functions don't exist)
   ```bash
   pytest tests/export/test_records.py tests/export/test_slug_generator.py -x -v
   ```
   Expected: All tests fail with ModuleNotFoundError or AttributeError

3. **Combined Export Tests**: Verify all export tests from Plan 01 and 01b
   ```bash
   pytest tests/export/ --collect-only -q | grep "test_"
   ```
   Expected: Tests for accounts, categories, persons, templates, records, slug generation (25+ total)

4. **Slug Edge Cases**: Verify slug generator tests cover mergeability scenarios
   ```bash
   pytest tests/export/test_slug_generator.py --collect-only
   ```
   Expected: Tests for gaps, different days, missing slugs, format validation
</verification>

<success_criteria>
1. Two test files created (records, slug generator)
2. All 11+ tests failing as expected (RED phase of TDD)
3. Tests cover monthly grouping (FMT-03) and slug generation (FMT-02)
4. Slug generator tests cover edge cases for merge-by-ID strategy
5. Tests are ready for implementation phase (GREEN phase in Plan 02)
6. Combined with Plan 01, full export test suite complete
</success_criteria>

<output>
After completion, create `.planning/phases/01-foundation/01-01b-SUMMARY.md` with:
- Number of tests created
- Test coverage for records and slug generation
- Confirmation that all tests fail (RED phase complete)
- Note: Combined with Plan 01, all export tests complete (25+ tests total)
</output>
