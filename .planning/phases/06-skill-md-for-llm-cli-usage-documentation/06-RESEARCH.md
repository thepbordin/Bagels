# Phase 6: SKILL.md for LLM CLI Usage Documentation - Research

**Researched:** 2026-03-22
**Domain:** Technical documentation authoring for LLM-consumed CLI reference
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**File Placement**
- Place at repository root: `SKILL.md`
- Root is most discoverable — agent tools like Claude Code auto-read root-level markdown

**File Format**
- Structured Markdown with command reference + examples
- Top-level summary of what Bagels CLI is and does
- Sections per command group (query, llm, schema, records/mutations)
- Each command: list all flags/options + one concrete invocation

**Self-Containment**
- Fully self-contained — all commands, flags, and examples in one file
- LLM must not need to read README or any other doc to use the CLI

**Commands to Document**
- All current CLI commands: query (records, summary, spending, trends, accounts, categories), llm context, schema, add record
- Include the `--at` flag for custom database paths (useful for multi-instance usage)
- Do NOT document removed commands: `bagels git`, `bagels export`, `bagels import`

**Detail Level per Command**
- All flags/options listed with types and descriptions
- One concrete example invocation per command (exact shell syntax, real-looking values)

**Workflow Patterns Section**
- Four named LLM workflows with exact shell invocations:
  1. Monthly financial snapshot — `bagels llm context --month YYYY-MM`
  2. Spending analysis — query records + spending by category for LLM trend analysis
  3. Budget check — query summary and compare against budget categories
  4. Add a record from LLM — `bagels records add` with structured flags from user intent
- Show exact shell commands (copy-pasteable by an LLM into a Bash tool)

### Claude's Discretion
- Exact prose in the top-level intro section
- Section ordering within the file
- Whether to include a "Getting Started" or "Prerequisites" mini-section
- Whether output format examples (YAML/JSON snippets) are shown inline

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 6 is a pure documentation task: create a single `SKILL.md` at the repository root that serves as a complete, self-contained reference for any LLM using Bagels via a Bash tool. No code changes are made.

The research task is to read all CLI source files, enumerate every command, subcommand, flag, and type exactly as implemented — then structure that into a format an LLM can consume. All source material lives in `src/bagels/cli/` and `src/bagels/__main__.py`. Everything below is derived from direct source inspection.

The primary challenge is accuracy: SKILL.md is only valuable if flag names, types, and mutual-exclusion rules are verbatim correct. The secondary challenge is usability: the workflow patterns section must show concrete, copy-pasteable commands that actually work.

**Primary recommendation:** Read all CLI source files first, then write SKILL.md in a single pass using the verified flag signatures below. Do not guess at flag names — use the exact strings from the Click decorators.

---

## Standard Stack

No new libraries are introduced. This phase uses:

| Tool | Version | Purpose |
|------|---------|---------|
| Markdown | — | SKILL.md authoring format |
| Click (existing) | already installed | CLI framework whose decorators are the source of truth for flag names and types |

**Installation:** None required.

---

## Complete Command Inventory (Verified from Source)

This is the authoritative command reference the planner and implementer must use. Derived directly from source inspection of all CLI files.

### Global Flags (on `bagels` root group — `__main__.py`)

| Flag | Type | Description |
|------|------|-------------|
| `--at PATH` | `click.Path` (file or dir) | Override data/config root directory |
| `--migrate CHOICE` | `actualbudget` | Run a one-time migration from another tool |
| `--source PATH` | `click.Path` (file only) | Source database for `--migrate` |

`--at` is the most important global flag for LLM workflows — it lets an LLM target a non-default data directory.

Running `bagels` (no subcommand) launches the interactive TUI. All subcommands listed below are non-interactive and safe for LLM use.

---

### `bagels init`

**Source:** `src/bagels/cli/init.py`

No flags. Initializes config directory, data directory, and SQLite database at the configured location.

**Example:**
```bash
bagels init
bagels --at ./my-instance init
```

---

### `bagels llm context`

**Source:** `src/bagels/cli/llm.py`

**Mutual exclusion rule:** Only one of `--month`, `--period`, or `--days` may be specified at a time. Defaults to current month if none specified.

| Flag | Short | Type | Description |
|------|-------|------|-------------|
| `--month` | `-m` | string `YYYY-MM` | Month for context dump |
| `--period` | — | choice: `all`, `30d`, `60d`, `90d` | Named time period |
| `--days` | — | int | Number of recent days |

**Output:** YAML to stdout. Includes: snapshot_date, period, accounts (list), summary (income/expenses/net/record_count), spending_by_category, recent_records (capped at 30), budget_status, categories (flat list with nature/color/parent/monthly_budget).

**Example:**
```bash
bagels llm context --month 2026-03
bagels llm context --period 30d
bagels llm context --days 14
bagels --at ./work-finances llm context --month 2026-03
```

---

### `bagels schema full`

**Source:** `src/bagels/cli/schema.py`

No flags. Outputs full YAML schema for all models: Account, Category, Person, Record, RecordTemplate. Each model section includes field list (name, type, nullable, primary_key, foreign_key) and relationships.

**Example:**
```bash
bagels schema full
```

---

### `bagels schema model MODEL_NAME`

**Source:** `src/bagels/cli/schema.py`

| Argument/Flag | Type | Description |
|---------------|------|-------------|
| `MODEL_NAME` | positional choice: `account`, `category`, `person`, `record`, `template` | Model to inspect |
| `--format` / `-f` | choice: `yaml`, `json` | Output format (default: yaml) |

**Example:**
```bash
bagels schema model record
bagels schema model record --format json
bagels schema model account
```

---

### `bagels summary`

**Source:** `src/bagels/cli/summary.py`

| Flag | Short | Type | Description |
|------|-------|------|-------------|
| `--month` | `-m` | string `YYYY-MM` | Month to summarize (default: current month) |
| `--format` | `-f` | choice: `table`, `json`, `yaml` | Output format (default: table) |

**Output fields (json/yaml):** month, total_income, total_expenses, net_savings, record_count.

**Example:**
```bash
bagels summary --month 2026-03 --format yaml
bagels summary --format json
```

---

### `bagels records list`

**Source:** `src/bagels/cli/records.py`

| Flag | Short | Type | Description |
|------|-------|------|-------------|
| `--category` | `-c` | string | Filter by category name |
| `--month` | `-m` | string `YYYY-MM` | Filter by month |
| `--date-from` | — | string `YYYY-MM-DD` | Start date (inclusive) |
| `--date-to` | — | string `YYYY-MM-DD` | End date (inclusive) |
| `--amount` | — | string `low..high` | Amount range (e.g., `100..500`) |
| `--account` | `-a` | string | Filter by account name |
| `--person` | `-p` | string | Filter by person name |
| `--format` | `-f` | choice: `table`, `json`, `yaml` | Output format (default: table) |
| `--limit` | — | int | Max records to return (default: 50) |
| `--all` | — | flag | Disable limit, return all matches |

**Note:** Only returns non-transfer records (transferToAccountId IS NULL). Results ordered by date descending.

**Example:**
```bash
bagels records list --month 2026-03 --format yaml
bagels records list --category food --limit 20 --format json
bagels records list --date-from 2026-01-01 --date-to 2026-03-31 --all --format json
bagels records list --amount 100..500 --account "Kasikorn Checking"
```

---

### `bagels records show RECORD_ID`

**Source:** `src/bagels/cli/records.py`

| Argument/Flag | Type | Description |
|---------------|------|-------------|
| `RECORD_ID` | positional string | Integer ID or slug (e.g., `r_2026-03-14_001`) |
| `--format` / `-f` | choice: `table`, `json`, `yaml` | Output format (default: table) |

**Example:**
```bash
bagels records show r_2026-03-14_001 --format yaml
bagels records show 42 --format json
```

---

### `bagels records add`

**Source:** `src/bagels/cli/records.py`

| Flag | Type | Description |
|------|------|-------------|
| `--from-yaml PATH` | file path (must exist) | Import records from a YAML file |

**YAML file formats accepted:**
- List of record dicts: `[{label, amount, date, ...}, ...]`
- Dict with `records` key: `{records: [...]}`
- Dict keyed by slugs: `{r_2026-03-14_001: {...}, ...}`

**Required fields per record:** `label` (string), `amount` (float), `date` (YYYY-MM-DD)

**Optional fields per record:** `accountSlug` (string), `categorySlug` (string), `personSlug` (string), `isIncome` (bool, default false), `isTransfer` (bool, default false)

**Important:** `accountSlug`, `categorySlug`, `personSlug` must match slugs already in the database. If validation errors exist for some records, the command will prompt whether to continue with valid records (interactive prompt — not fully LLM-safe for batch workflows).

**Example:**
```bash
bagels records add --from-yaml /tmp/new-records.yaml
```

---

### `bagels accounts list`

**Source:** `src/bagels/cli/accounts.py`

| Flag | Short | Type | Description |
|------|-------|------|-------------|
| `--format` | `-f` | choice: `table`, `json`, `yaml` | Output format (default: table) |

**Note:** Hidden accounts are excluded from output (hidden=true rows filtered).

**Example:**
```bash
bagels accounts list --format yaml
bagels accounts list --format json
```

---

### `bagels categories tree`

**Source:** `src/bagels/cli/categories.py`

| Flag | Short | Type | Description |
|------|-------|------|-------------|
| `--format` | `-f` | choice: `table`, `json`, `yaml` | Output format (default: table) |

**Output fields (json/yaml per category):** id, name, nature (CategoryNature enum string), color, depth, parent_id (if nested).

**Example:**
```bash
bagels categories tree --format yaml
bagels categories tree --format json
```

---

### `bagels spending by-category`

**Source:** `src/bagels/cli/spending.py`

| Flag | Short | Type | Description |
|------|-------|------|-------------|
| `--month` | `-m` | string `YYYY-MM` | Month to analyze (default: current month) |
| `--format` | `-f` | choice: `table`, `json`, `yaml` | Output format (default: table) |

**Output fields (json/yaml):** month, total (float), categories (list of {category, amount, percentage}).

**Example:**
```bash
bagels spending by-category --month 2026-03 --format yaml
bagels spending by-category --format json
```

---

### `bagels spending by-day`

**Source:** `src/bagels/cli/spending.py`

| Flag | Short | Type | Description |
|------|-------|------|-------------|
| `--month` | `-m` | string `YYYY-MM` | Month to analyze (default: current month) |
| `--format` | `-f` | choice: `table`, `json`, `yaml` | Output format (default: table) |

**Output fields (json/yaml):** month, total, daily_average, days (list of {date, amount}).

**Example:**
```bash
bagels spending by-day --month 2026-03 --format yaml
```

---

### `bagels trends`

**Source:** `src/bagels/cli/trends.py`

**Note:** `trends` is a top-level command, not a subcommand group.

| Flag | Short | Type | Description |
|------|-------|------|-------------|
| `--months` | `-m` | int (1–12, default: 3) | Number of months to compare |
| `--category` | `-c` | string | Filter to a specific category name |
| `--format` | `-f` | choice: `table`, `json`, `yaml` | Output format (default: table) |

**Output (no --category):** List of monthly summary objects with {month, total_income, total_expenses, net_savings, change_percentage, change_direction}.

**Output (with --category):** List of {month, amount} for that category only.

**Example:**
```bash
bagels trends --months 6 --format yaml
bagels trends --months 3 --category food --format json
```

---

### `bagels locate`

**Source:** `src/bagels/__main__.py`

| Argument | Type | Description |
|----------|------|-------------|
| `config` or `database` | positional choice | What path to print |

**Example:**
```bash
bagels locate database
bagels locate config
```

---

## Architecture Patterns

### Recommended SKILL.md Section Order

Based on LLM usage patterns — most common operations first:

```
1. What is Bagels CLI        (intro, 2-3 sentences)
2. Prerequisites             (optional — installation/setup note)
3. Global Flags              (--at is critical for multi-instance)
4. LLM Entry Point           (bagels llm context — primary command)
5. Schema Commands           (bagels schema — LLM orientation)
6. Query Commands            (read-only, structured output)
   - bagels summary
   - bagels records list / show
   - bagels accounts list
   - bagels categories tree
   - bagels spending by-category / by-day
   - bagels trends
7. Mutation Commands         (write operations)
   - bagels records add
8. Workflow Patterns         (four named LLM workflows)
```

### LLM-Friendly Documentation Pattern

For each command section, follow this structure:

```markdown
### `bagels <command> [subcommand]`

**Purpose:** One sentence.

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| ... | ... | ... | ... |

**Example:**
```bash
bagels <exact invocation>
```
```

This pattern is optimized for LLM token efficiency — table format for flags is scannable, example is copy-pasteable.

### Workflow Pattern Structure

Each workflow should include:
1. Named title (bold)
2. When to use it (one line)
3. Shell block with exact commands (no placeholders, use real-looking 2026-03 style dates)

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Enumerating flags | Re-reading source at plan time | Use the verified flag table in this RESEARCH.md |
| Workflow examples | Inventing commands | Use exact flag names from source — `--from-yaml` not `--file`, `by-category` not `--by-category` |

**Key insight:** The biggest documentation error risk is misremembering subcommand names. The `spending` group uses `by-category` and `by-day` as subcommands (not `--by-category` flag). The `schema` group uses `full` and `model` as subcommands. Implementer must verify against source, not memory.

---

## Common Pitfalls

### Pitfall 1: Wrong Subcommand vs Flag Naming
**What goes wrong:** Documenting `bagels spending --by-category` instead of `bagels spending by-category`. The spending and schema groups use Click subcommands, not flags.
**Why it happens:** The old `docs/FEATURE_ROADMAP.md` uses a `bagels query spending --by category` notation that was never the real implementation.
**How to avoid:** Use exact subcommand names from the Click `@group.command("name")` decorators, verified in this document.
**Warning signs:** Any example using `--by-category`, `--by-day`, or `bagels query` prefix is incorrect.

### Pitfall 2: Documenting Removed Commands
**What goes wrong:** Including `bagels git`, `bagels export`, or `bagels import` from the feature roadmap docs.
**Why it happens:** `docs/FEATURE_ROADMAP.md` describes the original vision, not the post-Phase-5 reality.
**How to avoid:** Only document commands registered in `__main__.py` via `cli.add_command()`. As of Phase 5, only: init, records, summary, accounts, categories, spending, trends, llm, schema, locate.
**Warning signs:** Any command not in the above list.

### Pitfall 3: Overstating `records add` for LLM Use
**What goes wrong:** Presenting `bagels records add` as fully LLM-safe when it has an interactive confirm prompt on partial validation failure.
**Why it happens:** Most Bagels commands are pure stdout, so the assumption carries over.
**How to avoid:** Note in SKILL.md that `records add --from-yaml` may prompt if some records fail validation. Recommend pre-validating YAML before calling.
**Warning signs:** Workflow pattern that assumes silent/unattended `records add` on arbitrary input.

### Pitfall 4: `bagels query` Prefix Does Not Exist
**What goes wrong:** Writing `bagels query records` or `bagels query summary` based on the feature roadmap notation.
**Why it happens:** `docs/FEATURE_ROADMAP.md` uses `bagels query X` as the CLI design spec, but implementation registered commands directly on the root group (summary, accounts, categories, spending, trends) or as subgroups (records).
**How to avoid:** Use `bagels records list`, `bagels summary`, `bagels accounts list`, etc. — the actual registered names.
**Warning signs:** Any invocation starting with `bagels query`.

### Pitfall 5: Trends vs Records Month Flag Semantics
**What goes wrong:** `bagels trends --months 6` means "compare 6 months of history", not "filter to month 6". This is different from `--month YYYY-MM` on other commands.
**Why it happens:** Flag name similarity.
**How to avoid:** Document the integer `--months` (count) vs string `--month` (YYYY-MM) distinction explicitly.

---

## Code Examples

Verified command signatures:

### Four Workflow Patterns (Locked by CONTEXT.md)

**Workflow 1: Monthly Financial Snapshot**
```bash
bagels llm context --month 2026-03
```
Dumps full YAML snapshot: accounts, summary, spending, recent records (last 30), budget status, categories.

**Workflow 2: Spending Analysis**
```bash
bagels records list --month 2026-03 --format yaml
bagels spending by-category --month 2026-03 --format yaml
```
Two commands together give records detail + category breakdown for LLM trend analysis.

**Workflow 3: Budget Check**
```bash
bagels summary --month 2026-03 --format yaml
bagels categories tree --format yaml
```
Summary shows net savings; categories tree shows monthly_budget fields for comparison.

**Workflow 4: Add a Record from LLM**
```bash
# Write a YAML file first (LLM generates this)
cat > /tmp/new-record.yaml << 'EOF'
- label: "Lunch at MBK"
  amount: 245.00
  date: "2026-03-22"
  accountSlug: "kasikorn-checking"
  categorySlug: "food-dining-out"
  isIncome: false
EOF
bagels records add --from-yaml /tmp/new-record.yaml
```

### The `--at` Flag Pattern (Multi-Instance Usage)
```bash
# All commands accept --at before the subcommand
bagels --at /path/to/project llm context --month 2026-03
bagels --at ./work-finances summary --format yaml
bagels --at ~/.local/share/bagels2 records list --format json
```

### Machine-Readable Output Pattern
```bash
# Use --format yaml or --format json on all query commands for LLM parsing
bagels accounts list --format yaml
bagels categories tree --format yaml
bagels spending by-category --month 2026-03 --format yaml
bagels trends --months 3 --format json
```

---

## Registered Command Tree (Verified)

Exact commands registered in `src/bagels/__main__.py`:

```
bagels                          (TUI when no subcommand)
  --at PATH
  --migrate CHOICE
  --source PATH
bagels init
bagels locate (config|database)
bagels llm
  bagels llm context
    --month/-m YYYY-MM
    --period (all|30d|60d|90d)
    --days INT
bagels schema
  bagels schema full
  bagels schema model (account|category|person|record|template)
    --format/-f (yaml|json)
bagels summary
  --month/-m YYYY-MM
  --format/-f (table|json|yaml)
bagels records
  bagels records list
    --category/-c STR
    --month/-m YYYY-MM
    --date-from YYYY-MM-DD
    --date-to YYYY-MM-DD
    --amount STR (low..high)
    --account/-a STR
    --person/-p STR
    --format/-f (table|json|yaml)
    --limit INT
    --all FLAG
  bagels records show RECORD_ID
    --format/-f (table|json|yaml)
  bagels records add
    --from-yaml PATH
bagels accounts
  bagels accounts list
    --format/-f (table|json|yaml)
bagels categories
  bagels categories tree
    --format/-f (table|json|yaml)
bagels spending
  bagels spending by-category
    --month/-m YYYY-MM
    --format/-f (table|json|yaml)
  bagels spending by-day
    --month/-m YYYY-MM
    --format/-f (table|json|yaml)
bagels trends
  --months/-m INT (1-12, default 3)
  --category/-c STR
  --format/-f (table|json|yaml)
```

---

## Validation Architecture

`nyquist_validation` is enabled in `.planning/config.json`.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | `pyproject.toml` or `pytest.ini` (existing project) |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

This phase is documentation-only. There is no code logic to unit test. The only validation is:

| ID | Behavior | Test Type | Automated Command | File Exists? |
|----|----------|-----------|-------------------|-------------|
| DOC-01 | `SKILL.md` exists at repository root | smoke | `test -f SKILL.md && echo ok` | Wave 0 |
| DOC-02 | All documented commands are registered in `__main__.py` | manual review | N/A — manual | N/A |
| DOC-03 | All documented flag names match Click decorator strings | manual review | N/A — manual | N/A |

**Note:** No automated tests are needed for this phase beyond verifying the file was created. The planner should not create a test task for documentation content — flag accuracy is enforced by the planner reading this research document.

### Wave 0 Gaps
- None — no new test infrastructure needed for a documentation-only phase.

---

## Open Questions

1. **Should `bagels locate` be documented in SKILL.md?**
   - What we know: It is a real, registered command. It outputs the config or database file path.
   - What's unclear: Whether an LLM would ever need to call it.
   - Recommendation: Include it briefly under a "Utility Commands" subsection. Low-cost addition that may help an LLM self-orient.

2. **Should SKILL.md show sample YAML output?**
   - What we know: Claude's Discretion in CONTEXT.md says "Whether output format examples (YAML/JSON snippets) are shown inline" is Claude's call.
   - Recommendation: Show one brief output snippet for `bagels llm context` (the most complex output) to orient the LLM on output shape. Keep others as flag tables + example invocations only.

3. **Should the `--migrate` flag be documented?**
   - What we know: It exists on the root group but is a one-time migration tool (actualbudget).
   - Recommendation: Omit from SKILL.md. It is not part of regular LLM-assisted workflows and adds noise.

---

## Sources

### Primary (HIGH confidence)
- `src/bagels/cli/llm.py` — llm context command, all flags verified
- `src/bagels/cli/records.py` — records group (list, show, add), all flags verified
- `src/bagels/cli/schema.py` — schema group (full, model), all flags verified
- `src/bagels/cli/summary.py` — summary command, all flags verified
- `src/bagels/cli/accounts.py` — accounts group (list), all flags verified
- `src/bagels/cli/categories.py` — categories group (tree), all flags verified
- `src/bagels/cli/spending.py` — spending group (by-category, by-day), all flags verified
- `src/bagels/cli/trends.py` — trends command, all flags verified
- `src/bagels/__main__.py` — root group, `--at` flag, all subcommand registrations verified
- `src/bagels/cli/init.py` — init command verified (no flags)
- `.planning/phases/06-skill-md-for-llm-cli-usage-documentation/06-CONTEXT.md` — locked decisions

### Secondary (MEDIUM confidence)
- `docs/FEATURE_ROADMAP.md` — design philosophy (used for context only; actual command names differ)

---

## Metadata

**Confidence breakdown:**
- Command inventory: HIGH — verified directly from Click source code
- Flag names and types: HIGH — copied verbatim from Click decorators
- Workflow patterns: HIGH — all four specified in CONTEXT.md, invocations derive from verified commands
- Documentation structure: HIGH — derived from CONTEXT.md locked decisions + Claude's Discretion areas

**Research date:** 2026-03-22
**Valid until:** Stable (documentation-only phase; only changes if CLI source changes)
