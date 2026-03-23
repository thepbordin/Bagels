# Phase 4: Verification - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Validate system reliability through comprehensive integration testing across the full stack — bidirectional sync (TEST-01), Git conflict resolution (TEST-02), CLI output formats (TEST-03), auto-export triggers (TEST-04), and LLM context completeness (TEST-05). This phase adds integration-level tests that bridge the gap between existing mocked unit tests and real end-to-end behavior. No new features — only verification.

</domain>

<decisions>
## Implementation Decisions

### Bidirectional Sync (TEST-01)
- **3 round-trip cycles**: SQLite → YAML → SQLite × 3; three cycles catches accumulation drift without excessive runtime
- **All field values match**: Every field on every entity (amounts, labels, dates, foreign key slug references) must be identical pre- and post-cycle
- **Slug IDs preserved**: `r_YYYY-MM-DD_###` IDs must survive round-trips unchanged — critical for merge-by-ID strategy
- **Edge case — corrupt YAML**: Malformed YAML must fail gracefully with a clear error; must not silently corrupt the database
- **Backup verification**: Confirm a backup file exists at `~/.local/share/bagels/backups/` after each import — validates the Phase 1 safety net

### Git Conflict Simulation (TEST-02)
- **Real git operations**: Use two tmp_git_repo clones (extending the pattern in `tests/git/conftest.py`), make diverging changes, merge — produces actual conflict markers
- **Import fails with clear error**: When YAML contains `<<<<<<< HEAD` markers, `bagels import` must detect them, refuse to import, print which file has conflicts, and tell the user to resolve manually
- **Post-resolution re-import**: After the user edits YAML to resolve the conflict, re-running import must succeed and the resolved data must land correctly in SQLite
- **`bagels git pull` conflict test**: Simulate a conflicting remote; verify `bagels git pull` stops gracefully and tells the user to resolve before re-running import

### Auto-Export Trigger Integration (TEST-04)
- **Integration tests (no mocks)**: Call manager CRUD methods directly against a real in-memory DB + real temp directory; verify actual YAML files are written to disk — bridges existing mocked unit tests in `test_hooks.py`
- **All 5 entity types**: Records, accounts, categories, persons, and templates all trigger YAML export; integration tests cover all five
- **Non-blocking guarantee**: Force git to fail (bad remote or no repo) and confirm CRUD operations still succeed and return correctly — validates Phase 3's non-blocking guarantee
- **Records CRUD exhaustive**: create, update, and delete operations each verified with real file output; monthly YAML grouping confirmed

### CLI Output & LLM Context (TEST-03, TEST-05)
- **Scope**: Not selected for discussion — Claude's discretion on approach
- Pattern from prior phases: pytest-based CLI tests using `CliRunner` already established in `tests/cli/`

### Claude's Discretion
- Exact snapshot vs schema-validation approach for CLI output format tests (TEST-03)
- LLM context completeness check method — field presence scan vs structural assertion (TEST-05)
- Test ordering and grouping within pytest modules
- Whether to add a top-level integration test directory or colocate tests in existing subdirectories

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`tests/conftest.py`** — `in_memory_db`, `temp_directory`, `sample_account`, `sample_records` fixtures; reuse directly for integration tests
- **`tests/git/conftest.py`** — `tmp_git_repo` fixture using `gitpython`; extend with two-repo setup for conflict simulation
- **`tests/cli/conftest.py`** — `CliRunner` setup with `set_custom_root` and `init_db` pattern; reuse for CLI output tests
- **`tests/automation/test_hooks.py`** — Mocked trigger tests already cover guard conditions (CONFIG=None, git.enabled=False, exception swallowing); Phase 4 adds integration layer on top

### Established Patterns
- **TDD red-green throughout**: All prior phases wrote tests first; Phase 4 adds integration tests post-implementation
- **`tmp_git_repo` pattern**: Real gitpython `Repo.init` with user config set — extend to two clones for conflict simulation
- **`CliRunner` + `set_custom_root`**: CLI tests isolate to temp directories using `bagels.locations.set_custom_root`
- **In-memory SQLite + temp dir**: Standard test isolation pattern; use for integration trigger tests

### Integration Points
- **Manager layer** (`src/bagels/managers/`) — trigger integration tests call CRUD here against real DB + real temp dir
- **Import layer** (`src/bagels/importer/importer.py`) — conflict detection test targets `run_full_import()`
- **Git operations** (`src/bagels/git/operations.py`) — conflict simulation and pull tests use real git repos
- **CLI entry** (`src/bagels/__main__.py`) — CLI output tests invoke commands via `CliRunner`

</code_context>

<specifics>
## Specific Ideas

- Conflict simulation should mirror the real multi-device workflow: device A edits record → commits, device B edits same record → commits, A pulls B's changes → conflict in YAML → user resolves → re-imports
- Integration trigger tests are the key gap: `test_hooks.py` mocks everything but never touches disk; Phase 4 tests must verify a real file appears at the right path with correct content

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 04-verification*
*Context gathered: 2026-03-19*
