# Bagels CLI — LLM Reference

Bagels is a local-first personal finance tracker backed by SQLite. The CLI provides non-interactive, structured-output commands safe for LLM use via Bash tool. Running `bagels` with no subcommand launches the interactive TUI (not for LLM use).

---

## Global Flags

These flags are placed **before** any subcommand.

| Flag | Type | Description |
|------|------|-------------|
| `--at PATH` | path | Override data/config root directory. Place before any subcommand. |

Example: `bagels --at /path/to/project llm context --month 2026-03`

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

### `bagels records add`

**Purpose:** Add a record using inline flags or batch-import from a YAML file.

**Inline mode (no `--yaml`):** Creates a single record from flags. Missing required fields are prompted interactively.

| Flag | Type | Description |
|------|------|-------------|
| `--label` | string | Record label/description |
| `--amount` | float | Amount (must be > 0) |
| `--date` | `YYYY-MM-DD` | Record date (defaults to today if prompted) |
| `--account-id` | int | Account ID |
| `--category-id` | int | Category ID (optional) |
| `--person-id` | int | Person ID (optional) |
| `--income` | flag | Mark as income record |
| `--transfer` | flag | Mark as transfer |
| `--transfer-to-account-id` | int | Destination account ID for transfers |
| `--format` / `-f` | `table\|json\|yaml` | Output format (default: table) |

```bash
bagels records add --label "Lunch" --amount 245 --date 2026-03-22 --account-id 1
bagels records add --label "Salary" --amount 50000 --account-id 1 --income
```

**Batch mode (`--yaml PATH`):** Import one or more records from a YAML file.

| Flag | Type | Description |
|------|------|-------------|
| `--yaml PATH` | file path (must exist) | YAML file containing records to import |

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
bagels records add --yaml /tmp/new-record.yaml
```

### `bagels records update IDENTIFIER`

**Purpose:** Update an existing record by integer ID or slug.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug (e.g., `r_2026-03-22_001`) |
| `--label` | string | — | New record label |
| `--amount` | float | — | New amount |
| `--date` | `YYYY-MM-DD` | — | New date |
| `--account-id` | int | — | New account ID |
| `--category-id` | int | — | New category ID |
| `--person-id` | int | — | New person ID |
| `--income/--no-income` | flag | — | Set income flag |
| `--transfer/--no-transfer` | flag | — | Set transfer flag |
| `--transfer-to-account-id` | int | — | New transfer destination account ID |
| `--format` / `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels records update 42 --amount 300 --format json
bagels records update r_2026-03-22_001 --label "Updated label"
```

### `bagels records delete IDENTIFIER`

**Purpose:** Delete a record by integer ID or slug. Hard delete.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--force` | flag | — | Skip confirmation prompt |

```bash
bagels records delete 42 --force
bagels records delete r_2026-03-22_001
```

---

## Entity CRUD Commands

### Accounts

#### `bagels accounts add`

**Purpose:** Create a new account.

| Flag | Type | Description |
|------|------|-------------|
| `--name` | string | Account name (prompted if missing) |
| `--balance` | float | Beginning balance (prompted if missing) |
| `--description` | string | Account description (optional) |
| `--hidden` | flag | Mark account as hidden |
| `--format` / `-f` | `table\|json\|yaml` | Output format (default: table) |

```bash
bagels accounts add --name "Savings" --balance 10000
bagels accounts add --name "Cash" --balance 0 --format json
```

#### `bagels accounts show IDENTIFIER`

**Purpose:** Show details for a single account.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--format` / `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels accounts show 1 --format json
bagels accounts show acc_savings
```

#### `bagels accounts update IDENTIFIER`

**Purpose:** Update an existing account.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--name` | string | — | New account name |
| `--balance` | float | — | New beginning balance |
| `--description` | string | — | New account description |
| `--hidden/--no-hidden` | flag | — | Set account visibility |
| `--format` / `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels accounts update 1 --name "New Savings"
bagels accounts update 1 --hidden --format yaml
```

#### `bagels accounts delete IDENTIFIER`

**Purpose:** Soft-delete an account.

**Note:** Soft delete. `--cascade` soft-deletes all linked records. Without `--cascade`, delete is blocked if linked records exist.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--force` | flag | — | Skip confirmation prompt |
| `--cascade` | flag | — | Soft-delete all linked records |

```bash
bagels accounts delete 1 --force
bagels accounts delete 1 --cascade --force
```

---

### Categories

#### `bagels categories list`

**Purpose:** List all categories.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels categories list --format yaml
```

#### `bagels categories show IDENTIFIER`

**Purpose:** Show details for a single category.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--format` / `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels categories show 5 --format json
```

#### `bagels categories add`

**Purpose:** Create a new category.

| Flag | Type | Description |
|------|------|-------------|
| `--name` | string | Category name (prompted if missing) |
| `--nature` | `Want\|Need\|Must` | Category nature (prompted if missing) |
| `--color` | string | Hex color (e.g., `#FF5733`) |
| `--parent-id` | int | Parent category ID (optional) |
| `--format` / `-f` | `table\|json\|yaml` | Output format (default: table) |

```bash
bagels categories add --name "Dining Out" --nature Need --parent-id 5
bagels categories add --name "Salary" --nature Must
```

#### `bagels categories update IDENTIFIER`

**Purpose:** Update an existing category.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--name` | string | — | New category name |
| `--nature` | `Want\|Need\|Must` | — | New category nature |
| `--color` | string | — | New hex color |
| `--parent-id` | int | — | New parent category ID |
| `--format` / `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels categories update 5 --name "Food & Dining"
```

#### `bagels categories delete IDENTIFIER`

**Purpose:** Delete a category.

**Note:** Use `--cascade` to also soft-delete linked records. Subcategories are not automatically deleted.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--force` | flag | — | Skip confirmation prompt |
| `--cascade` | flag | — | Soft-delete all linked records |

```bash
bagels categories delete 5 --force
bagels categories delete 5 --cascade
```

---

### Persons

#### `bagels persons list`

**Purpose:** List all persons.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels persons list --format yaml
```

#### `bagels persons add`

**Purpose:** Create a new person.

| Flag | Type | Description |
|------|------|-------------|
| `--name` | string | Person name (prompted if missing) |
| `--format` / `-f` | `table\|json\|yaml` | Output format (default: table) |

```bash
bagels persons add --name "Alice"
```

#### `bagels persons show IDENTIFIER`

**Purpose:** Show details for a single person.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--format` / `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels persons show 1 --format json
```

#### `bagels persons update IDENTIFIER`

**Purpose:** Update an existing person.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--name` | string | — | New person name |
| `--format` / `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels persons update 1 --name "Bob"
```

#### `bagels persons delete IDENTIFIER`

**Purpose:** Delete a person.

**Note:** Use `--cascade` to soft-delete linked records (via splits).

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--force` | flag | — | Skip confirmation prompt |
| `--cascade` | flag | — | Soft-delete linked records |

```bash
bagels persons delete 1 --force
bagels persons delete 1 --cascade
```

---

### Templates

#### `bagels templates list`

**Purpose:** List all record templates.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels templates list --format yaml
```

#### `bagels templates add`

**Purpose:** Create a new record template.

| Flag | Type | Description |
|------|------|-------------|
| `--label` | string | Template label (prompted if missing) |
| `--amount` | float | Template amount (prompted if missing) |
| `--account-id` | int | Account ID (prompted if missing) |
| `--category-id` | int | Category ID (optional) |
| `--income` | flag | Mark as income |
| `--transfer` | flag | Mark as transfer |
| `--transfer-to-account-id` | int | Transfer target account ID |
| `--format` / `-f` | `table\|json\|yaml` | Output format (default: table) |

```bash
bagels templates add --label "Rent" --amount 15000 --account-id 1
bagels templates add --label "Salary" --amount 50000 --account-id 1 --income
```

#### `bagels templates show IDENTIFIER`

**Purpose:** Show details for a single template.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--format` / `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels templates show 1 --format json
```

#### `bagels templates update IDENTIFIER`

**Purpose:** Update an existing record template.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--label` | string | — | New template label |
| `--amount` | float | — | New amount |
| `--account-id` | int | — | New account ID |
| `--category-id` | int | — | New category ID |
| `--income/--no-income` | flag | — | Set income flag |
| `--transfer/--no-transfer` | flag | — | Set transfer flag |
| `--transfer-to-account-id` | int | — | New transfer target account ID |
| `--format` / `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels templates update 1 --amount 16000
```

#### `bagels templates delete IDENTIFIER`

**Purpose:** Hard-delete a record template.

**Note:** Templates are permanently deleted (hard delete).

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--force` | flag | — | Skip confirmation prompt |

```bash
bagels templates delete 1 --force
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

### 4. Add a Record from LLM (Batch YAML)

**When:** Create expense records from natural language user intent using YAML file.

```bash
cat > /tmp/new-record.yaml << 'EOF'
- label: "Lunch at MBK"
  amount: 245.00
  date: "2026-03-22"
  accountSlug: "kasikorn-checking"
  categorySlug: "food-dining-out"
  isIncome: false
EOF
bagels records add --yaml /tmp/new-record.yaml
```

### 5. Create a Record from CLI Flags

**When:** Quickly add a single expense/income without a YAML file.

```bash
bagels accounts list --format yaml    # get account IDs
bagels categories tree --format yaml  # get category IDs
bagels records add --label "Coffee" --amount 120 --date 2026-03-22 --account-id 1 --category-id 3
```

---

## Tips

- Use `--format yaml` or `--format json` on any query command for machine-readable output.
- The `--at` flag goes before the subcommand: `bagels --at /path llm context`.
- `bagels llm context` is the single best command for getting full financial context in one call.
- `bagels schema full` orients you to all field names before writing mutation YAML.
- `bagels accounts list --format yaml` and `bagels categories tree --format yaml` give you valid slugs to use in `records add` YAML.
- `IDENTIFIER` in CRUD commands accepts either integer ID or slug string.
- All create/update commands support `--format` for output format.
- Delete commands prompt for confirmation by default; use `--force` to skip.
- `--cascade` on delete also removes linked records (soft-delete). Records themselves are hard-deleted (exception to soft-delete pattern).
