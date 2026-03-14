---
phase: 01-foundation
plan: 03
subsystem: testing
tags: [pytest, tdd, yaml-import, validation, merge-by-id]

# Dependency graph
requires:
  - 01-01: Test infrastructure and entity models
provides:
  - Failing tests for YAML validation logic (TDD RED phase)
  - Failing tests for import operations with merge-by-ID strategy (TDD RED phase)
affects: [01-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TDD RED/GREEN/REFACTOR workflow
    - Validation before import (fail-fast on broken refs)
    - Merge-by-ID strategy (YAML is authoritative)
    - Slug-based relationship resolution
    - Backup creation before import

key-files:
  created:
    - tests/import/test_validator.py
    - tests/import/test_import.py
  modified: []

key-decisions:
  - "Validation tests cover all entity types with comprehensive error reporting"
  - "Merge-by-ID strategy ensures YAML is authoritative over SQLite data"
  - "Fail-fast on broken references prevents orphaned records"
  - "Backup creation enables recovery from failed imports"
  - "Slug-based references preserve relationships across import/export cycles"

patterns-established:
  - "Pattern 1: Validation returns (is_valid, errors) tuple for comprehensive error reporting"
  - "Pattern 2: Import functions validate first, then import (fail-fast on errors)"
  - "Pattern 3: Merge-by-ID updates existing records by slug, adds new records"
  - "Pattern 4: Relationships resolved via slug lookups (accountSlug → accountId)"
  - "Pattern 5: Backup creation uses timestamp-based filenames"

requirements-completed: [DATA-06, FMT-01, FMT-02, FMT-03, FMT-05]

# Metrics
duration: 4min
completed: 2026-03-14
---

# Phase 01 Plan 03 Summary

**TDD RED phase for YAML import functionality with validation, merge-by-ID strategy, and referential integrity checks**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-14T16:53:00Z
- **Completed:** 2026-03-14T16:57:12Z
- **Tasks:** 2/2 completed
- **Files modified:** 2 created

## Accomplishments

- Created comprehensive test suite for YAML validation logic (11 tests)
- Created comprehensive test suite for YAML import operations (12 tests)
- Established merge-by-ID strategy tests (YAML is authoritative)
- Validated fail-fast behavior on broken references
- Tested backup creation before import operations
- Verified all 23 tests fail correctly (RED phase confirmed)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create YAML validation tests** - `4a27bd7` (test)
2. **Task 2: Create import tests with merge-by-ID strategy** - `d680d5d` (test)

**Plan metadata:** (to be added in final commit)

_Note: All commits are test commits (TDD RED phase). Implementation commits will follow in Plan 04._

## Files Created/Modified

- `tests/import/test_validator.py` - 11 test cases for YAML validation logic
- `tests/import/test_import.py` - 12 test cases for import operations with merge-by-ID

## Test Coverage

### Validation Tests (test_validator.py)

- **Accounts:** 3 tests (structure validation, missing fields, timestamp format)
- **Records:** 3 tests (broken foreign keys, monetary values, slug format)
- **Categories:** 2 tests (structure validation, broken parent references)
- **Persons:** 1 test (structure validation)
- **Templates:** 1 test (structure validation with relationships)
- **Error Reporting:** 1 test (comprehensive error reporting, not fail-fast)

### Import Tests (test_import.py)

- **Accounts:** 2 tests (import new accounts, backup creation)
- **Records:** 8 tests (merge-by-ID, add new records, monthly files, relationships, fail-fast, validation, idempotent, bulk efficiency)
- **Categories:** 1 test (parent-child relationships)
- **Templates:** 1 test (order preservation)

**Total:** 23 tests (exceeds 19+ requirement from plan)

## Deviations from Plan

### Auto-fixed Issues

None - plan executed exactly as written.

## Issues Encountered

None - all tests fail as expected with ModuleNotFoundError (RED phase working correctly).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Test infrastructure complete for import functionality
- All 23 tests failing correctly (RED phase complete)
- Ready for Plan 04: Implement import functions (GREEN phase)
- Tests serve as executable documentation for import behavior
- Validation tests ensure fail-fast on broken references
- Merge-by-ID tests ensure YAML is authoritative

## Verification Results

```bash
# Test discovery
pytest tests/import/ --collect-only
# Result: 23 tests collected

# RED phase confirmation
pytest tests/import/ -x -v
# Result: All tests fail with ModuleNotFoundError (expected)

# Requirement coverage
grep -r "DATA-06\|FMT-" tests/import/
# Result: 4 requirement references found
```

## Test Scenarios Covered

### Validation Scenarios

1. Required field validation (name missing)
2. Foreign key reference validation (broken accountSlug, parentSlug)
3. Data type validation (timestamp format, monetary values)
4. Slug format validation (r_YYYY-MM-DD_### pattern)
5. Comprehensive error reporting (all errors listed, not fail-fast)

### Import Scenarios

1. Import new entities (accounts, records, categories, templates)
2. Merge-by-ID strategy (update existing records by slug)
3. Add new records alongside existing ones
4. Handle monthly record files (2026-03.yaml with 10+ records)
5. Preserve relationships via slug references (accountSlug → accountId)
6. Fail-fast on broken references (ValidationError, no partial import)
7. Validate before importing (all errors reported together)
8. Create backup before import (backups/backup_YYYY-MM-DD_HHMMSS.db)
9. Handle category parent-child relationships (parentSlug → parentCategoryId)
10. Handle templates with order (preserve ordinal field)
11. Idempotent imports (second import produces same state)
12. Efficient bulk operations (1000 records in <10 seconds)

## Edge Cases Covered

- Missing required fields (name, beginningBalance, etc.)
- Invalid data types (string instead of float, invalid timestamps)
- Invalid slug format (not r_YYYY-MM-DD_###)
- Broken foreign key references (accountSlug, parentSlug not found)
- Multiple validation errors (comprehensive reporting)
- Merge conflicts (YAML overwrites SQLite)
- Duplicate imports (idempotent behavior)
- Large datasets (1000+ records)
- Referential integrity (no orphaned records)

---
*Phase: 01-foundation*
*Completed: 2026-03-14*
