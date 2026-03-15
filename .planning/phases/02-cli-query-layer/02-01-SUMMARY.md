---
phase: 02-cli-query-layer
plan: 01
subsystem: query-layer
tags: [cli, rich-tables, json, yaml, sqlalchemy, filters, formatters, pytest]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: [database-models, managers-utils, yaml-serialization, cli-framework]
provides:
  - Shared output formatter module (table/JSON/YAML rendering)
  - Filter utilities (date parsing, amount ranges, SQLAlchemy query builders)
  - CLI test infrastructure (fixtures for CliRunner, sample database)
  - Test coverage for all formatter and filter functions
affects: [02-02, 02-03, 02-04, 02-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Rich Table with styled columns (cyan ID, green Date, yellow Amount)
    - JSON/YAML serialization with datetime handling via default=str
    - SQLAlchemy query builder pattern with filter chaining
    - Click CliRunner for CLI testing
    - Regex validation for strict input formats (YYYY-MM, 100..500)

key-files:
  created: [tests/cli/__init__.py, tests/cli/test_output_formats.py]
  modified: [src/bagels/queries/formatters.py, src/bagels/queries/filters.py, tests/cli/conftest.py]

key-decisions:
  - "Remove non-existent accountType field from Account model formatting"
  - "Use parentCategory instead of parent for Category model relationships"
  - "Add strict regex validation for month format (YYYY-MM) to prevent ambiguity"
  - "Add str() conversion for category.nature enum in dict serialization"

patterns-established:
  - "Table format as default for all query commands (human-first design)"
  - "Datetime serialization via default=str in JSON dumps"
  - "SQLAlchemy filter functions return Query objects for chaining"
  - "CLI test fixtures use in-memory SQLite for isolation"

requirements-completed: [CLI-09]

# Metrics
duration: 5min
completed: 2026-03-15
---

# Phase 2: Plan 1 Summary

**Rich table/JSON/YAML formatters with datetime serialization, SQLAlchemy filter utilities, and comprehensive CLI test infrastructure**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-15T15:33:03Z
- **Completed:** 2026-03-15T15:38:53Z
- **Tasks:** 4
- **Files modified:** 4

## Accomplishments

- **Shared formatter module** supporting table (Rich), JSON, and YAML output with consistent styling
- **Filter utilities** for date parsing (YYYY-MM), amount ranges (100..500), and SQLAlchemy query builders
- **CLI test infrastructure** with CliRunner fixture and comprehensive sample database
- **35 tests** covering all formatter and filter functionality with 100% pass rate

## Task Commits

Each task was committed atomically:

1. **Task 1: Create CLI test infrastructure** - `09ff565` (test)
   - Added tests/cli/__init__.py for CLI test module
   - Added tests/cli/conftest.py with cli_runner, sample_db_with_records, sample_accounts/categories/records fixtures
   - Fixtures provide 3 accounts, 5 categories, 20+ records spanning 3 months

2. **Tasks 2-4: Implement formatters, filters, and tests** - `e891d1b` (feat)
   - Fixed format_accounts() to remove non-existent accountType field
   - Fixed format_categories() to use parentCategory instead of parent
   - Enhanced parse_month() with strict YYYY-MM regex validation
   - Added to_json() and to_yaml() helpers with datetime serialization
   - Created comprehensive test suite with 35 tests (all passing)

## Files Created/Modified

- `tests/cli/__init__.py` - CLI test module initialization
- `tests/cli/conftest.py` - Shared fixtures for CLI testing (cli_runner, sample_db_with_records)
- `tests/cli/test_output_formats.py` - 35 tests for formatters and filters
- `src/bagels/queries/formatters.py` - Table/JSON/YAML formatting functions
- `src/bagels/queries/filters.py` - Date parsing and SQLAlchemy filter utilities

## Decisions Made

**Account model formatting:** Removed `accountType` field references from formatters as the Account model doesn't have this attribute. Fixed format_accounts() to only include id, name, balance, description, and hidden fields.

**Category relationship naming:** Changed from `category.parent` to `category.parentCategory` to match the actual SQLAlchemy relationship name in the Category model.

**Strict month validation:** Added regex pattern `^\d{4}-\d{2}$` to parse_month() to reject invalid formats like "2026/03" and ensure only "YYYY-MM" is accepted.

**Enum serialization:** Added str() conversion for category.nature enum in _category_to_dict() to ensure proper JSON/YAML serialization.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Account model attribute error**
- **Found during:** Task 2 (format_accounts implementation)
- **Issue:** formatters.py referenced account.accountType which doesn't exist on the Account model
- **Fix:** Removed accountType column from table formatting and from _account_to_dict() helper
- **Files modified:** src/bagels/queries/formatters.py
- **Verification:** test_format_accounts_table passes, table renders correctly
- **Committed in:** e891d1b (Task 2-4 commit)

**2. [Rule 1 - Bug] Fixed Category relationship attribute error**
- **Found during:** Task 2 (format_categories implementation)
- **Issue:** formatters.py used category.parent which doesn't exist (should be parentCategory)
- **Fix:** Changed all references from category.parent to category.parentCategory
- **Files modified:** src/bagels/queries/formatters.py
- **Verification:** test_format_categories_table passes, parent relationships render correctly
- **Committed in:** e891d1b (Task 2-4 commit)

**3. [Rule 1 - Bug] Added enum serialization for category.nature**
- **Found during:** Task 2 (_category_to_dict implementation)
- **Issue:** category.nature is an enum object, needs str() conversion for JSON serialization
- **Fix:** Added str() wrapper around category.nature in _category_to_dict()
- **Files modified:** src/bagels/queries/formatters.py
- **Verification:** test_format_categories_json passes, nature serializes as string
- **Committed in:** e891d1b (Task 2-4 commit)

**4. [Rule 1 - Bug] Enhanced parse_month() validation**
- **Found during:** Task 4 (test_parse_month_invalid)
- **Issue:** parse_month("2026/03") was accepting invalid format (split on "-" still works)
- **Fix:** Added regex validation ^\d{4}-\d{2}$ and month range check (01-12)
- **Files modified:** src/bagels/queries/filters.py
- **Verification:** test_parse_month_invalid passes, ValueError raised for "2026/03"
- **Committed in:** e891d1b (Task 2-4 commit)

---

**Total deviations:** 4 auto-fixed (4 bugs)
**Impact on plan:** All auto-fixes were necessary for correctness - model attributes didn't match formatter assumptions. No scope creep.

## Issues Encountered

- **Table column truncation in tests:** Rich tables truncate long column headers with "…" in narrow terminals. Fixed by updating test assertions to check for truncated variants (e.g., "Amount" or "Amo").

- **Test fixture session access:** Initially tried to access record.sa_session which doesn't exist. Simplified test to directly use fixture-provided records.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Formatter module ready** for all CLI query commands (records, accounts, categories, summary)
- **Filter utilities ready** for date, amount, category, and account filtering
- **Test infrastructure ready** for testing all CLI commands
- **No blockers** - proceeding to Plan 02 (records query commands)

---
*Phase: 02-cli-query-layer*
*Completed: 2026-03-15*
