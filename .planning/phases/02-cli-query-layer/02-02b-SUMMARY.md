---
phase: "02"
plan: "02b"
title: "Batch Import Records from YAML"
one_liner: "CLI command for batch importing records from YAML files with validation, foreign key resolution, and progress feedback"
status: "complete"
tags: ["cli", "records", "import", "yaml", "validation"]
start_epoch: 1773588678
end_epoch: 1773589045
duration_seconds: 367
completed_date: "2026-03-15"
wave: 1
depends_on: []
requirements: ["CLI-10"]
---

# Phase 02 Plan 02b: Batch Import Records from YAML Summary

## Overview

Implement batch import functionality for records from YAML files, enabling users to quickly add multiple records at once. This provides efficient bulk data entry for records via YAML files, useful for migrating data from other systems, entering historical data, or rapid prototyping.

## Implementation Summary

### Task 1: Implement Batch Import from YAML

**File Modified:** `src/bagels/cli/records.py`

Added `bagels records add --from-yaml` command with comprehensive features:

1. **YAML Format Support:**
   - List format: `[{label: ..., amount: ..., date: ..., accountSlug: ..., categorySlug: ...}, ...]`
   - Dict format: `{records: [{...}, ...]}`
   - Dict format with slugs: `{r_2026-03-14_001: {...}, ...}`

2. **Validation:**
   - Required fields: `label`, `amount`, `date`
   - Date format validation (YYYY-MM-DD)
   - Foreign key validation (accountSlug, categorySlug, personSlug)
   - Displays validation errors before importing
   - Shows count of valid vs invalid records

3. **Import Logic:**
   - Resolves foreign keys (slug → ID)
   - Generates unique slugs for new records using `generate_record_slug()`
   - Batch commits every 100 records for performance
   - Handles partial failures gracefully

4. **Progress Feedback:**
   - Rich progress bar during validation and import
   - Displays count of imported records
   - Shows validation errors if any
   - Success message with total count

### Task 2: Integration Tests

**File Modified:** `tests/cli/test_records.py`

Created 9 comprehensive integration tests:

1. **Basic Import Tests:**
   - `test_add_from_yaml`: List format import
   - `test_add_from_yaml_dict_format`: Dict format with records key
   - `test_add_from_yaml_empty`: Empty YAML file handling
   - `test_add_from_yaml_multiple`: Multiple record import

2. **Validation Tests:**
   - `test_add_from_yaml_validation`: Validation error display
   - `test_add_from_yaml_missing_fields`: Missing required fields
   - `test_add_from_yaml_invalid_date`: Invalid date format

3. **Foreign Key Tests:**
   - `test_add_from_yaml_foreign_keys`: FK resolution (accountSlug, categorySlug)
   - `test_add_from_yaml_invalid_fk`: Non-existent foreign keys

**Test Infrastructure:**
- Updated `tests/cli/conftest.py` to use Session mocking for CLI tests
- Fixed enum values (Nature.NEED/WANT instead of strings)
- Added slugs to test fixtures (accounts, categories)

## Deviations from Plan

### Rule 1 - Bug: Fixed test conftest enum values
- **Found during:** Task 2
- **Issue:** Test fixture used string values ('Need', 'Want') instead of enum values (Nature.NEED, Nature.WANT)
- **Fix:** Updated conftest.py to import and use Nature enum
- **Files modified:** `tests/cli/conftest.py`
- **Commit:** Included in test commit

### Rule 1 - Bug: Fixed test conftest field names
- **Found during:** Task 2
- **Issue:** Test fixture used `parentId` instead of `parentCategoryId` for Category model
- **Fix:** Updated to use correct field name `parentCategoryId`
- **Files modified:** `tests/cli/conftest.py`
- **Commit:** Included in test commit

### Rule 3 - Auto-fix blocking issue: Missing slug generation for test fixtures
- **Found during:** Task 2
- **Issue:** Test fixtures didn't generate slugs for accounts and categories, causing FK validation to fail
- **Fix:** Added slug field to all Account and Category creations in conftest.py
- **Files modified:** `tests/cli/conftest.py`
- **Commit:** Included in test commit

### Rule 3 - Auto-fix blocking issue: Session mocking needed for CLI tests
- **Found during:** Task 2
- **Issue:** CLI commands were using the real database file instead of test database
- **Fix:** Used `unittest.mock.patch` to mock `bagels.cli.records.Session` to return test database session
- **Files modified:** `tests/cli/test_records.py`
- **Commit:** Already applied in previous commit (74334cf)

## Key Decisions

### 1. YAML Format Flexibility
**Decision:** Support multiple YAML formats (list, dict with records key, dict with slugs)
**Rationale:** Provides flexibility for users. List format is simplest for manual entry, dict formats match existing export patterns.
**Impact:** Increased code complexity but improved UX

### 2. Validation Before Import
**Decision:** Validate all records before importing any
**Rationale:** Prevents partial imports with hidden errors. Users can fix all issues before retrying.
**Impact:** Better data integrity, slight delay before import starts

### 3. Partial Import Support
**Decision:** Allow continuing with valid records even if some fail validation
**Rationale:** Useful when importing large batches where a few records have issues
**Impact:** Added user prompt for confirmation, more complex error handling

### 4. Batch Commits
**Decision:** Commit every 100 records instead of all at once
**Rationale:** Better memory usage for large imports, prevents transaction timeouts
**Impact:** Minor complexity increase, significant performance improvement for large files

## Technical Context

### Files Created
- None (all changes to existing files)

### Files Modified
- `src/bagels/cli/records.py`: Added `add_record` command (389 lines added, 506 lines removed due to formatting)
- `tests/cli/test_records.py`: Added 9 batch import tests (270 lines added)
- `tests/cli/conftest.py`: Fixed enum values, field names, added slugs (minor changes)

### Tech Stack
- **Click:** CLI framework for command structure
- **Rich:** Progress bars and styled output
- **PyYAML:** YAML file parsing
- **SQLAlchemy:** Database operations and slug generation
- **Pytest:** Testing framework with CliRunner and mocking

### Integration Points
- **Records Manager:** Uses `create_record()` from `bagels.managers.records`
- **Slug Generator:** Uses `generate_record_slug()` from `bagels.export.slug_generator`
- **Models:** Works with Record, Account, Category, Person models
- **Session:** Uses `Session()` from `bagels.models.database.app`

## Success Criteria

- [x] Add command imports records from YAML file
- [x] Validation catches missing fields, invalid dates, non-existent foreign keys
- [x] Progress feedback displays during import
- [x] Foreign keys resolve correctly
- [x] Test coverage for all validation scenarios (9 tests)
- [x] Works with Plan 02-02a records command group

## Metrics

- **Duration:** 6 minutes 7 seconds
- **Tasks Completed:** 2/2
- **Tests Added:** 9 integration tests
- **Lines of Code:** ~660 lines added (implementation + tests)
- **Commits:** 2 (implementation + tests)
- **Requirements Met:** CLI-10

## Verification

### Manual Testing
```bash
# Create test YAML file
cat > test_records.yaml << EOF
- label: "Grocery Shopping"
  amount: 150.50
  date: "2026-03-15"
  accountSlug: "checking"
  categorySlug: "groceries"

- label: "Gas Station"
  amount: 45.00
  date: "2026-03-16"
  accountSlug: "credit-card"
  categorySlug: "transport"
EOF

# Import records
bagels records add --from-yaml test_records.yaml

# Verify import
bagels records list --month 2026-03
```

### Automated Testing
```bash
# Run all batch import tests
pytest tests/cli/test_records.py -k "add_from_yaml" -v

# Result: 9 passed
```

## Next Steps

Plan 02-02b is complete. Next plan in Phase 02:
- **Plan 02-03:** Accounts query commands (list, show)

## Self-Check: PASSED

### Commits Verified
- [x] bb14522: feat(02-02b): implement batch import from YAML
- [x] 74334cf: test(02-02a): add Session mocking to CLI tests (includes 02-02b tests)

### Files Verified
- [x] src/bagels/cli/records.py exists with add_record command
- [x] tests/cli/test_records.py exists with 9 batch import tests
- [x] All tests passing (9/9)

### Requirements Verified
- [x] CLI-10 requirement met with working `bagels records add --from-yaml` command

---

*Plan completed: 2026-03-15 in 6 minutes 7 seconds*
