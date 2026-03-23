# Phase 5: Requirement Reduction, remove buggy git and yaml loader - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Reduce Bagels to SQLite-only operation by removing Git sync and YAML storage/sync pathways (both automatic and manual), while preserving YAML strictly as a query output format for CLI responses.

This phase clarifies how to remove/retire existing behavior. It does not add new product capabilities.

</domain>

<decisions>
## Implementation Decisions

### Reduction Boundary
- Remove all Git features and all YAML sync/storage features, including both automatic and manual pathways.
- Keep YAML support only for CLI output formatting (e.g., `--format yaml` in query/read commands).
- Remove command registration and command modules for `bagels git`, `bagels export`, and `bagels import`.

### Command Behavior After Removal
- Removed commands should behave as normal unknown commands (default CLI behavior).
- Do not add explicit removal notes in top-level CLI help.
- Do not provide compatibility shims for removed commands.

### Existing YAML/Git Data Handling
- Leave existing YAML files on disk untouched.
- Leave existing Git repositories in data directories untouched.
- Silently ignore legacy YAML/Git artifacts (no recurring or one-time startup notices for file detection).
- Do not add a new backup workflow in this phase.

### Config Handling
- Keep `git.*` fields in config parsing for compatibility.
- Add a one-time deprecation warning at startup for Git/YAML sync config behavior.

### Success Criteria and Quality Gate
- SQLite-only runtime with no reachable Git/YAML sync code paths.
- Remove dead sync code and related tests in this same phase.
- Add reduction-focused requirements and mark old Git/YAML sync requirements as superseded.
- Full test gate: `uv run pytest` must pass.

### Claude's Discretion
- Exact mechanism for tracking one-time warning display (state key/location).
- Exact warning copy and where it is emitted during startup.
- Documentation/changelog wording and placement details.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope and Requirement Baseline
- `.planning/ROADMAP.md` — Phase 5 definition and milestone ordering.
- `.planning/REQUIREMENTS.md` — Existing requirement inventory to supersede/update during reduction.
- `.planning/PROJECT.md` — Current product direction and constraints.
- `.planning/STATE.md` — Current phase/milestone state and roadmap evolution notes.

### Prior Decisions Being Reversed or Constrained
- `.planning/phases/01-foundation/01-CONTEXT.md` — Original YAML-as-canonical and import/export decisions.
- `.planning/phases/03-automation/03-CONTEXT.md` — Original Git automation and startup import decisions.
- `.planning/phases/04-verification/04-CONTEXT.md` — Existing verification expectations around Git/YAML pathways.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/bagels/__main__.py` — Top-level CLI command registration (primary removal entry point for git/export/import commands).
- `src/bagels/config.py` — `GitConfig` and config-load flow; contains compatibility and warning hook opportunities.
- `src/bagels/app.py` — startup worker (`run_startup_import`) currently performs pull/import sync path.
- `src/bagels/cli/git.py`, `src/bagels/cli/export.py`, `src/bagels/cli/import.py` — direct manual sync command modules.
- `src/bagels/managers/accounts.py`, `src/bagels/managers/categories.py`, `src/bagels/managers/persons.py`, `src/bagels/managers/record_templates.py`, `src/bagels/managers/records.py` — background auto-export/auto-commit hooks.
- `src/bagels/importer/importer.py` and `src/bagels/export/exporter.py` — YAML sync implementation surface to retire from runtime path.

### Established Patterns
- Manager-layer side effects run in daemon threads and swallow exceptions to keep CRUD non-blocking.
- CLI command groups are registered centrally in `__main__.py`.
- Data-path resolution is centralized in `src/bagels/locations.py`.
- Integration and automation tests already cover startup import, git operations, conflict checks, and auto-export hooks.

### Integration Points
- Remove command wiring in `__main__.py` and retire/de-scope sync CLI modules.
- Remove or neutralize startup import/pull behavior in `app.py`.
- Remove manager-triggered export/commit hooks to stop background sync side effects.
- Keep YAML formatter paths in query commands untouched.
- Rebaseline tests to SQLite-only behavior and preserve coverage for remaining CLI/TUI features.

</code_context>

<specifics>
## Specific Ideas

- "Requirement Reduction, remove buggy git and yaml loader" is treated as a deliberate rollback of sync complexity to stabilize the core SQLite product.
- Keep user-facing YAML output for read/query workflows to preserve scripting ergonomics.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 05-requirement-reduction-remove-buggy-git-and-yaml-loader*
*Context gathered: 2026-03-21*
