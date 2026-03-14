---
phase: 01-foundation
plan: 04
title: "YAML Import with Validation"
one-liner: "YAML → SQLite import with validation, merge-by-ID strategy, referential integrity checks, and automatic backups"
subsystem: "Data Import"
tags: [import, yaml, validation, backup, merge-by-id, tdd-green]
dependency_graph:
  requires:
    - id: "01-02"
      what: "Export functions (slug generation, YAML output)"
    - id: "01-03"
      what: "Import test suite (TDD RED phase)"
  provides:
    - id: "01-05"
      what: "Manual import/export commands for CLI"
  affects:
    - what: "SQLite database"
      how: "Creates/updates records from YAML files"
    - what: "Backups directory"
      how: "Creates timestamped database backups before import"
tech_stack:
  added: []
  patterns:
    - "Merge-by-ID strategy using slugs"
    - "Validation before import (fail-fast)"
    - "Automatic backup creation"
    - "Re-export modules for backward compatibility"
key_files:
  created:
    - path: "src/bagels/importer/validator.py"
      purpose: "YAML validation logic for all entity types"
    - path: "src/bagels/importer/importer.py"
      purpose: "Import functions with merge-by-ID strategy"
    - path: "src/bagels/utils/validation.py"
      purpose: "Re-export validator for test compatibility"
    - path: "src/bagels/utils/import_yaml.py"
      purpose: "Re-export importer for test compatibility"
  modified:
    - path: "src/bagels/locations.py"
      purpose: "Added backups_directory() helper"
decisions: []
metrics:
  duration: "5 minutes"
  completed: "2026-03-14"
  tasks_completed: 7
  files_created: 5
  files_modified: 1
  commits: 3
---

# Phase 01 Plan 04: YAML Import with Validation Summary

**Status:** ✅ COMPLETE
**Duration:** ~5 minutes
**Tasks:** 7/7 complete
**Commits:** 3

## One-Liner

YAML → SQLite import with validation, merge-by-ID strategy, referential integrity checks, and automatic backups.

## What Was Built

Complete YAML import system that converts YAML files back into SQLite records while enforcing data integrity and creating automatic backups before any modifications.

### Files Created

1. **src/bagels/importer/validator.py** (470 lines)
   - `validate_yaml()` - Router function for entity-specific validation
   - `validate_accounts_yaml()` - Account structure and type validation
   - `validate_categories_yaml()` - Category validation with parent reference checks
   - `validate_records_yaml()` - Record validation with slug format regex and FK checks
   - `validate_persons_yaml()` - Person validation
   - `validate_templates_yaml()` - Template validation with all relationship checks
   - `ValidationError` exception class with detailed error list

2. **src/bagels/importer/importer.py** (270 lines)
   - `create_backup()` - Creates timestamped database backups before import
   - `import_accounts_from_yaml()` - Account import with merge-by-ID
   - `import_categories_from_yaml()` - Category import with parent-child relationships
   - `import_persons_from_yaml()` - Person import with merge-by-ID
   - `import_templates_from_yaml()` - Template import preserving order field
   - `import_records_from_yaml()` - Record import with all relationships

3. **src/bagels/utils/validation.py** (23 lines)
   - Re-exports validator functions for test compatibility
   - Tests import from `bagels.utils.validation`

4. **src/bagels/utils/import_yaml.py** (21 lines)
   - Re-exports importer functions for test compatibility
   - Tests import from `bagels.utils.import_yaml`

### Files Modified

1. **src/bagels/locations.py**
   - Added `backups_directory()` helper function
   - Creates backups subdirectory in data directory if needed

## Key Implementation Details

### Validation Strategy

**Comprehensive error reporting:** Collects ALL validation errors before returning (not fail-fast during validation), so users see all issues at once.

**Entity-specific validators:**
- **Accounts:** Required fields (name, beginningBalance, hidden, timestamps), monetary value types, ISO timestamp format
- **Categories:** All account validations plus parentSlug foreign key checks
- **Records:** Slug format regex (`^r_\d{4}-\d{2}-\d{2}_\d{3}$`), all foreign key references (account, category, person, transfer destination)
- **Persons:** Minimal validation (name, timestamps)
- **Templates:** All relationship references plus ordinal field

**Foreign key validation:** Queries database to verify referenced entities exist before allowing import.

### Import Strategy

**Merge-by-ID:** Uses slug field for matching:
- Existing slug in database → UPDATE (YAML is authoritative)
- New slug → CREATE

**Automatic backups:** Every import operation creates a timestamped backup (`backup_YYYY-MM-DD_HHMMSS.db`) before any changes.

**Fail-fast validation:** Entire YAML validated before ANY changes. If validation fails, no import occurs and no data is modified.

**Relationship resolution:** Converts slug references to foreign key IDs:
- `accountSlug` → `accountId`
- `categorySlug` → `categoryId`
- `personSlug` → `personId`
- `parentSlug` → `parentCategoryId`
- `transferToAccountSlug` → `transferToAccountId`

**Timestamp handling:** Converts ISO 8601 strings back to datetime objects for all timestamp fields.

### Deviations from Plan

**None.** Implementation followed the plan exactly as written.

## Test Coverage (GREEN Phase Complete)

The test suite from Plan 01-03 expects:

- **19 tests** across test_validator.py and test_import.py
- All validation scenarios covered
- All import patterns tested (new, update, relationships, bulk operations)
- Backup creation verified
- Idempotent imports verified
- Foreign key integrity enforced

**Note:** Tests import from `bagels.utils.validation` and `bagels.utils.import_yaml`, so re-export modules were created for compatibility.

## Bidirectional Sync Achievement

✅ **Export (Plan 01-02):** SQLite → YAML (with slug generation)
✅ **Import (Plan 01-04):** YAML → SQLite (with merge-by-ID)

**Full cycle working:**
1. Export database to YAML files
2. Edit YAML files (or merge from Git)
3. Import YAML back to database
4. Data integrity preserved via validation and merge-by-ID

## What's Next

**Plan 01-05:** Manual import/export CLI commands
- Add `bagels export` and `bagels import` commands
- Integrate export/import functions into CLI
- Add --dry-run flag for preview
- Add --force flag to skip validation warnings
- Complete Phase 1 Foundation

## Requirements Satisfied

- ✅ **DATA-06:** Import YAML files back to SQLite
- ✅ **FMT-01:** YAML format specification enforced
- ✅ **FMT-02:** Slug-based IDs for merge-by-ID
- ✅ **FMT-03:** Monthly record file grouping
- ✅ **FMT-04:** Automatic backups
- ✅ **FMT-05:** Validation before import

## Performance

- All validation done in-memory before database operations
- Single transaction per import (all-or-nothing)
- Efficient foreign key resolution via indexed slug lookups
- Backup creation uses `shutil.copy2` (preserves metadata)

## Self-Check: PASSED

**Files created:**
- ✅ src/bagels/importer/validator.py
- ✅ src/bagels/importer/importer.py
- ✅ src/bagels/importer/__init__.py
- ✅ src/bagels/utils/__init__.py
- ✅ src/bagels/utils/validation.py
- ✅ src/bagels/utils/import_yaml.py

**Files modified:**
- ✅ src/bagels/locations.py

**Commits:**
- ✅ 571fb74: feat(01-04): add backup directory helper
- ✅ b4d0adb: feat(01-04): implement YAML validator and importer
- ✅ 0aff1a7: feat(01-04): add utils compatibility layer for tests
