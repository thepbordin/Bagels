# Phase 6: SKILL.md for LLM CLI Usage Documentation - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Create a single `SKILL.md` file at the repository root that teaches an LLM how to use the Bagels CLI. Covers all current commands with flags and one example each, plus named workflow patterns showing exact shell invocations an LLM would run. Documentation-only phase — no code changes.

</domain>

<decisions>
## Implementation Decisions

### File Placement
- Place at repository root: `SKILL.md`
- Root is most discoverable — agent tools like Claude Code auto-read root-level markdown

### File Format
- Structured Markdown with command reference + examples
- Top-level summary of what Bagels CLI is and does
- Sections per command group (query, llm, schema, records/mutations)
- Each command: list all flags/options + one concrete invocation

### Self-Containment
- Fully self-contained — all commands, flags, and examples in one file
- LLM must not need to read README or any other doc to use the CLI

### Commands to Document
- All current CLI commands: query (records, summary, spending, trends, accounts, categories), llm context, schema, add record
- Include the `--at` flag for custom database paths (useful for multi-instance usage)
- Do NOT document removed commands: `bagels git`, `bagels export`, `bagels import`

### Detail Level per Command
- All flags/options listed with types and descriptions
- One concrete example invocation per command (exact shell syntax, real-looking values)

### Workflow Patterns Section
- Four named LLM workflows with exact shell invocations:
  1. **Monthly financial snapshot** — `bagels llm context --month YYYY-MM`
  2. **Spending analysis** — query records + spending by category for LLM trend analysis
  3. **Budget check** — query summary and compare against budget categories
  4. **Add a record from LLM** — `bagels records add` with structured flags from user intent
- Show exact shell commands (copy-pasteable by an LLM into a Bash tool)

### Claude's Discretion
- Exact prose in the top-level intro section
- Section ordering within the file
- Whether to include a "Getting Started" or "Prerequisites" mini-section
- Whether output format examples (YAML/JSON snippets) are shown inline

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements are fully captured in decisions above.

### CLI Source Files (read to enumerate accurate flags and command signatures)
- `src/bagels/cli/llm.py` — `bagels llm context` command (--month, --period, --days)
- `src/bagels/cli/records.py` — `bagels records` command group (add, list, etc.)
- `src/bagels/cli/schema.py` — `bagels schema` command
- `src/bagels/cli/spending.py` — `bagels query spending` command
- `src/bagels/cli/summary.py` — `bagels query summary` command
- `src/bagels/cli/trends.py` — `bagels query trends` command
- `src/bagels/cli/accounts.py` — `bagels accounts` command
- `src/bagels/cli/categories.py` — `bagels categories` command
- `src/bagels/__main__.py` — top-level CLI group, `--at` flag registration

### Project Context
- `.planning/ROADMAP.md` — Phase 6 definition
- `docs/FEATURE_ROADMAP.md` — LLM CLI design philosophy and intended command set

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/bagels/cli/llm.py`: `bagels llm context` already implemented — document as primary LLM entry point
- `src/bagels/cli/schema.py`: schema command exists — document for LLM context building
- All query CLI commands already implemented and stable after Phase 5

### Established Patterns
- CLI uses Click with `--format` flags (table/json/yaml) on query commands
- `--at` is a global flag on the root `bagels` group
- All query commands are pure stdout, no interactive prompts — safe for LLM pipe usage

### Integration Points
- SKILL.md is a standalone file with no code integration
- Must reflect the post-Phase-5 state: no git/export/import commands

</code_context>

<specifics>
## Specific Ideas

- No specific references or "I want it like X" moments — standard SKILL.md documentation approach
- Examples should use realistic-looking values (real month formats like 2026-03, realistic labels)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 06-skill-md-for-llm-cli-usage-documentation*
*Context gathered: 2026-03-21*
