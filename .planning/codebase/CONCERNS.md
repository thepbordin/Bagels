# Codebase Concerns

**Analysis Date:** 2026-03-14

## Tech Debt

**Type System Incompleteness:**
- Issue: Inconsistent typing throughout the codebase with multiple `# TODO: properly type everything` comments
- Files: `[src/bagels/home.py]`, `[src/bagels/forms/record_forms.py]`
- Impact: Type safety is compromised, leading to potential runtime errors and poor IDE support
- Fix approach: Add proper type annotations to all methods, replacing `Any` with specific types and implementing the commented TypedDict structures

**DataTable Column Generation:**
- Issue: Unhandled edge case when no columns exist before adding rows
- Files: `[src/bagels/components/datatable.py:1656]`
- Impact: Users will be required to manually call `add_column(s)` before `add_row`, causing runtime errors
- Fix approach: Implement automatic column generation when no columns exist during `add_row` calls

## Known Bugs

**Textual Framework Type Issues:**
- Bug: Textual's type definitions contain inconsistencies causing `type: ignore` workarounds
- Files: `[src/bagels/components/autocomplete.py:351]`
- Symptoms: Autocomplete layer styling requires type ignore, masking potential real type errors
- Trigger: Accessing `self.screen.styles.layers` property
- Workaround: Using `type: ignore` comment which hides potential issues

**Autocomplete Widget Fragility:**
- Bug: Autocomplete component lacks proper cleanup when reference widgets are destroyed
- Files: `[src/bagels/components/autocomplete.py:355]`
- Symptoms: May cause runtime errors or memory leaks when input widget is removed
- Trigger: Screen transitions or widget destruction
- Workaround: None documented, potential crash scenario

## Security Considerations

**SQL Injection Risk:**
- Risk: Raw SQL queries with string formatting in migration code
- Files: `[src/bagels/migrations/migrate_actualbudget.py]`
- Current mitigation: Using parameterized queries (appears safe from cursory review)
- Recommendations: Static analysis to verify all SQL queries are parameterized

**File System Access:**
- Risk: Configuration file operations without proper validation
- Files: `[src/bagels/config.py]`
- Current mitigation: Basic validation and error handling
- Recommendations: Add input sanitization for configuration values and file path validation

## Performance Bottlenecks

**Large DataTable Component:**
- Problem: 2789 lines in a single component file makes maintenance difficult
- Files: `[src/bagels/components/datatable.py]`
- Cause: All table functionality in one monolithic class
- Improvement path: Break into smaller components (Cell, Row, Table core, Rendering)

**Autocomplete Search Performance:**
- Problem: No debouncing on autocomplete searches
- Files: `[src/bagels/components/autocomplete.py:519]`
- Cause: Synchronous search without rate limiting
- Improvement path: Add debounce mechanism and async search capabilities

## Fragile Areas

**Textual Version Dependencies:**
- Component: Textual TUI framework integration
- Files: Multiple component files using Textual
- Why fragile: Heavy reliance on Textual's unstable APIs, requires many type ignores
- Safe modification: Thorough testing after any Textual version upgrade
- Test coverage: Present but may not catch all API breakage scenarios

**Plotext Integration:**
- Component: Custom plot functionality
- Files: `[src/bagels/components/tplot/]`
- Why fragile: Plotext library appears to have bugs requiring workarounds
- Safe modification: Careful testing of rendering functionality
- Test coverage: Visual regression tests needed

## Scaling Limits

**Memory Usage:**
- Current capacity: Unknown but large DataTable could cause memory issues with many rows
- Limit: DataTable component uses in-memory storage, not optimized for large datasets
- Scaling path: Consider virtual scrolling and pagination for large datasets

**File Size Growth:**
- Current capacity: Single DataTable component at 2789 lines is becoming unwieldy
- Limit: Component complexity increases linearly with features
- Scaling path: Break into smaller, focused components

## Dependencies at Risk

**Textual Framework:**
- Risk: Active development with potential breaking changes
- Impact: Multiple components would need updates
- Migration plan: Monitor Textual releases and implement comprehensive testing

**Plotext Library:**
- Risk: Contains bugs requiring workarounds
- Impact: Custom plotting functionality may break
- Migration plan: Consider alternative plotting libraries or custom implementation

## Missing Critical Features

**Error Recovery:**
- Problem: Limited error recovery mechanisms in core components
- Blocks: Robust operation in edge cases
- Recommendation: Add comprehensive error handling and recovery logic

**Type Safety Coverage:**
- Problem: Missing type annotations throughout codebase
- Blocks: Development tooling and code quality
- Recommendation: Implement comprehensive typing strategy

## Test Coverage Gaps

**UI Component Testing:**
- What's not tested: Visual rendering and interactive behavior of custom components
- Files: `[src/bagels/components/]` directory
- Risk: UI regressions could break user experience
- Priority: High

**Integration Testing:**
- What's not tested: Component interactions and data flow between modules
- Files: Cross-component interactions
- Risk: Integration issues could go undetected
- Priority: Medium

---

*Concerns audit: 2026-03-14*