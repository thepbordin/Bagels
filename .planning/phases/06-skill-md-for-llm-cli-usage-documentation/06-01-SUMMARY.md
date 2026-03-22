---
phase: 06-skill-md-for-llm-cli-usage-documentation
plan: 01
subsystem: documentation
tags: [bagels, cli, llm, markdown, skill]

requires:
  - phase: 05-requirement-reduction-remove-buggy-git-and-yaml-loader
    provides: "Finalized CLI command set (removed git/export/import) that SKILL.md documents"
provides:
  - "SKILL.md at repository root: complete self-contained LLM reference for Bagels CLI"
  - "All 10+ commands documented with exact flag names, types, defaults, and examples"
  - "Four named LLM workflow patterns with copy-pasteable shell commands"
affects: [any LLM agent using Bagels via Bash tool]

tech-stack:
  added: []
  patterns:
    - "LLM-oriented documentation pattern: flag tables + single concrete example per command"

key-files:
  created:
    - SKILL.md
  modified: []

key-decisions:
  - "Placed SKILL.md at repository root for maximum LLM discoverability (auto-read by Claude Code)"
  - "Documented --at flag pattern prominently as it enables multi-instance LLM workflows"
  - "Added bagels schema commands first after intro to help LLM orient to data model before queries"
  - "Included interactive-prompt warning on records add to prevent LLM workflow hangs"

patterns-established:
  - "SKILL.md pattern: intro + global flags + LLM entry point + schema + query + mutation + workflows + tips"

requirements-completed: [DOC-01, DOC-02, DOC-03]

duration: 1min
completed: 2026-03-22
---

# Phase 6 Plan 01: SKILL.md LLM CLI Reference Summary

**Self-contained SKILL.md at repository root documenting all 10 Bagels CLI commands with flags, examples, four LLM workflow patterns, and a warning about the interactive prompt edge case in `records add`.**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-22T08:02:17Z
- **Completed:** 2026-03-22T08:03:29Z
- **Tasks:** 2 (1 auto + 1 checkpoint auto-approved)
- **Files modified:** 1

## Accomplishments

- Created SKILL.md at repository root with 56 "bagels" references covering all commands
- Documented all 10+ CLI commands with exact Click flag signatures from source
- Four named workflow patterns present with copy-pasteable shell commands
- No removed commands (git, export, import) or incorrect prefixes (query) appear anywhere

## Task Commits

1. **Task 1: Write SKILL.md with complete CLI reference and workflow patterns** - `eb3d04b` (feat)
2. **Task 2: Verify SKILL.md accuracy and completeness** - Auto-approved (auto_advance=true)

## Files Created/Modified

- `SKILL.md` - Complete LLM-facing CLI reference for Bagels: all commands, flags, examples, workflow patterns

## Decisions Made

- Used research-verified flag signatures from 06-RESEARCH.md rather than re-reading source — high confidence from prior verification
- Added `bagels schema full` / `bagels schema model` section early (before query commands) to help LLMs orient to data model before making queries
- Included a "Tips" section at end with three high-value LLM usage hints
- Documented `--at` flag with explicit before-subcommand placement note since this is a common LLM mistake

## Deviations from Plan

None - plan executed exactly as written. RESEARCH.md contained complete, verified flag signatures; SKILL.md was written in a single pass using those signatures.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 6 complete. SKILL.md is ready for use by any LLM agent. Future phases can reference SKILL.md as the authoritative CLI reference — update it whenever CLI commands change.

---
*Phase: 06-skill-md-for-llm-cli-usage-documentation*
*Completed: 2026-03-22*
