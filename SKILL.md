# Bagels CLI — LLM Reference

Bagels is a local-first personal finance tracker backed by SQLite. The CLI provides non-interactive, structured-output commands safe for LLM use via Bash tool. Running `bagels` with no subcommand launches the interactive TUI (not for LLM use).

---

## Global Flags

These flags are placed **before** any subcommand.

| Flag | Type | Description |
|------|------|-------------|
| `--at PATH` | path | Override data/config root directory. Place before any subcommand. |

Example: `bagels --at /path/to/project llm context --month 2026-03`

Do NOT document or use `--migrate` or `--source` (one-time migration tools, not for LLM workflows).

---

## LLM Entry Point — `bagels llm context`

**Purpose:** Dump a complete financial snapshot as YAML to stdout. This is the single best command for getting full financial context in one call.

**Mutual exclusion:** Only one of `--month`, `--period`, or `--days` may be specified at a time. Defaults to current month if none specified.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--month` | `-m` | `YYYY-MM` | current month | Month for context dump |
| `--period` | — | `all\|30d\|60d\|90d` | — | Named time period |
| `--days` | — | int | — | Number of recent days |

**Output includes:** snapshot_date, period, accounts, summary (income/expenses/net/record_count), spending_by_category, recent_records (capped at 30), budget_status, categories.

```bash
bagels llm context --month 2026-03
bagels llm context --period 30d
bagels llm context --days 14
bagels --at ./work-finances llm context --month 2026-03
```

---

## Schema Commands

### `bagels schema full`

**Purpose:** Output full YAML schema for all models (Account, Category, Person, Record, RecordTemplate).

No flags.

```bash
bagels schema full
```

### `bagels schema model MODEL_NAME`

**Purpose:** Output schema for a single model in YAML or JSON.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `MODEL_NAME` | positional: `account\|category\|person\|record\|template` | required | Model to inspect |
| `--format` / `-f` | `yaml\|json` | `yaml` | Output format |

```bash
bagels schema model record
bagels schema model record --format json
bagels schema model account
```

---

## Query Commands

All query commands support `--format/-f (table|json|yaml)`. Use `--format yaml` or `--format json` for machine-readable output.

### `bagels summary`

**Purpose:** Summarize income, expenses, and net savings for a month.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--month` | `-m` | `YYYY-MM` | current month | Month to summarize |
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

**Output fields (json/yaml):** month, total_income, total_expenses, net_savings, record_count.

```bash
bagels summary --month 2026-03 --format yaml
bagels summary --format json
```

### `bagels records list`

**Purpose:** List expense/income records with optional filters.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--category` | `-c` | string | — | Filter by category name |
| `--month` | `-m` | `YYYY-MM` | — | Filter by month |
| `--date-from` | — | `YYYY-MM-DD` | — | Start date (inclusive) |
| `--date-to` | — | `YYYY-MM-DD` | — | End date (inclusive) |
| `--amount` | — | string `low..high` | — | Amount range (e.g., `100..500`) |
| `--account` | `-a` | string | — | Filter by account name |
| `--person` | `-p` | string | — | Filter by person name |
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |
| `--limit` | — | int | `50` | Max records to return |
| `--all` | — | flag | — | Disable limit, return all matches |

**Note:** Only non-transfer records returned (transferToAccountId IS NULL). Results ordered by date descending.

```bash
bagels records list --month 2026-03 --format yaml
bagels records list --category food --limit 20 --format json
bagels records list --date-from 2026-01-01 --date-to 2026-03-31 --all --format json
bagels records list --amount 100..500 --account "Kasikorn Checking"
```

### `bagels records show RECORD_ID`

**Purpose:** Show details of a single record by ID or slug.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `RECORD_ID` | positional string | required | Integer ID or slug (e.g., `r_2026-03-14_001`) |
| `--format` / `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels records show r_2026-03-14_001 --format yaml
bagels records show 42 --format json
```

### `bagels accounts list`

**Purpose:** List all visible accounts.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

**Note:** Hidden accounts (hidden=true) are excluded from output.

```bash
bagels accounts list --format yaml
bagels accounts list --format json
```

### `bagels categories tree`

**Purpose:** Output the full category tree.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

**Output fields (json/yaml):** id, name, nature, color, depth, parent_id.

```bash
bagels categories tree --format yaml
bagels categories tree --format json
```

### `bagels spending by-category`

**Purpose:** Break down spending totals by category for a month.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--month` | `-m` | `YYYY-MM` | current month | Month to analyze |
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

**Output fields (json/yaml):** month, total, categories [{category, amount, percentage}].

```bash
bagels spending by-category --month 2026-03 --format yaml
bagels spending by-category --format json
```

### `bagels spending by-day`

**Purpose:** Break down daily spending totals for a month.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--month` | `-m` | `YYYY-MM` | current month | Month to analyze |
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

**Output fields (json/yaml):** month, total, daily_average, days [{date, amount}].

```bash
bagels spending by-day --month 2026-03 --format yaml
```

### `bagels trends`

**Purpose:** Compare monthly financial trends over multiple months.

**Note:** `--months` (plural, int 1-12) means "how many months of history" — this is NOT the same as `--month YYYY-MM` on other commands.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--months` | `-m` | int (1–12) | `3` | Number of months of history to compare |
| `--category` | `-c` | string | — | Filter to a specific category name |
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

**Output (no --category):** [{month, total_income, total_expenses, net_savings, change_percentage, change_direction}]

**Output (with --category):** [{month, amount}]

```bash
bagels trends --months 6 --format yaml
bagels trends --months 3 --category food --format json
```

---

## Mutation Commands

### `bagels records add --from-yaml PATH`

**Purpose:** Add one or more records from a YAML file.

| Flag | Type | Description |
|------|------|-------------|
| `--from-yaml PATH` | file path (must exist) | YAML file containing records to import |

**Accepted YAML formats:**
- List of dicts: `[{label, amount, date, ...}, ...]`
- Dict with `records` key: `{records: [...]}`
- Dict keyed by slugs: `{r_2026-03-14_001: {...}, ...}`

**Required fields per record:** `label` (string), `amount` (float), `date` (YYYY-MM-DD)

**Optional fields per record:** `accountSlug` (string), `categorySlug` (string), `personSlug` (string), `isIncome` (bool, default false), `isTransfer` (bool, default false)

**WARNING:** May prompt interactively if some records fail validation. Pre-validate YAML before calling.

```bash
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

---

## Utility Commands

### `bagels init`

**Purpose:** Initialize config, data directory, and SQLite database. No flags.

```bash
bagels init
bagels --at ./my-instance init
```

### `bagels locate (config|database)`

**Purpose:** Print the path to the config file or database file.

```bash
bagels locate config
bagels locate database
```

---

## Workflow Patterns

### 1. Monthly Financial Snapshot

**When:** Get a complete picture of one month's finances.

```bash
bagels llm context --month 2026-03
```

### 2. Spending Analysis

**When:** Analyze spending patterns for a month with detailed records and category breakdown.

```bash
bagels records list --month 2026-03 --format yaml
bagels spending by-category --month 2026-03 --format yaml
```

### 3. Budget Check

**When:** Compare actual spending against budget targets.

```bash
bagels summary --month 2026-03 --format yaml
bagels categories tree --format yaml
```

### 4. Add a Record from LLM

**When:** Create expense records from natural language user intent.

```bash
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

---

## Tips

- Use `--format yaml` or `--format json` on any query command for machine-readable output.
- The `--at` flag goes before the subcommand: `bagels --at /path llm context`.
- `bagels llm context` is the single best command for getting full financial context in one call.
- `bagels schema full` orients you to all field names before writing mutation YAML.
- `bagels accounts list --format yaml` and `bagels categories tree --format yaml` give you valid slugs to use in `records add` YAML.
