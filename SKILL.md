---
name: bagels-finance
description: Interacting with the Bagels personal finance tracker via its CLI. Use this when users want to track expenses, manage accounts, analyze spending, add records, or get financial summaries. Bagels is a local-first SQLite-backed finance tool with both a TUI and a non-interactive CLI suitable for LLM use.
---

Bagels is a local-first personal finance tracker backed by SQLite. The CLI provides non-interactive, structured-output commands safe for LLM use via Bash tool. Running `bagels` with no subcommand launches the interactive TUI (not for LLM use).

This happens in two steps:
1. Gather financial context (read operations)
2. Perform mutations (create/update/delete records, accounts, categories, etc.)

First, undertake this task:

## GATHERING FINANCIAL CONTEXT

To begin, always start by gathering the user's financial context before performing any actions.

### THE CRITICAL UNDERSTANDING
- What is received: A user request about their finances — spending analysis, record entry, budget check, etc.
- What to do first: Use `bagels llm context` to get a complete financial snapshot.
- What happens next: Use the snapshot to inform all subsequent commands — correct account IDs, category slugs, date ranges, and amounts.

The context dump is **the single most important command**. It gives you everything: accounts, categories, budgets, recent records, and spending summaries — all in one call.

### HOW TO GATHER CONTEXT

**Use `bagels llm context`** to get a full financial snapshot:

```bash
bagels llm context --month 2026-03
bagels llm context --period 30d
bagels llm context --days 14
```

**Mutual exclusion:** Only one of `--month`, `--period`, or `--days` may be specified. Defaults to current month if none given.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--month` | `-m` | `YYYY-MM` | current month | Month for context dump |
| `--period` | — | `all\|30d\|60d\|90d` | — | Named time period |
| `--days` | — | int | — | Number of recent days |

**Output includes:** snapshot_date, period, accounts, summary (income/expenses/net/record_count), spending_by_category, recent_records (capped at 30), budget_status, categories.

**recent_records fields:** id (slug), label, amount, net_amount (amount minus split totals), date, is_income, is_transfer, category, account, splits (list of {person, amount, is_paid, paid_date}).

**Global `--at` flag:** Override the data/config root directory. Place **before** any subcommand:
```bash
bagels --at /path/to/project llm context --month 2026-03
```

### ESSENTIAL PRINCIPLES
- **CONTEXT FIRST**: Always call `bagels llm context` before performing mutations — you need valid IDs and slugs.
- **MACHINE-READABLE OUTPUT**: Always use `--format yaml` or `--format json` on query commands.
- **IDENTIFIERS**: All CRUD commands accept either integer IDs or slug strings as identifiers.
- **NON-INTERACTIVE**: Provide all required flags to avoid interactive prompts. Use `--force` on deletes.
- **SINGLE SOURCE OF TRUTH**: The SQLite database is local-first. There is no cloud sync.

---

## SCHEMA INSPECTION

**CRITICAL STEP**: Before writing mutation YAML or creating records, inspect the schema to know all valid field names.

### `bagels schema full`

Output full YAML schema for all models (Account, Category, Person, Record, RecordTemplate). No flags.

```bash
bagels schema full
```

### `bagels schema model MODEL_NAME`

Output schema for a single model.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `MODEL_NAME` | positional: `account\|category\|person\|record\|template` | required | Model to inspect |
| `--format` / `-f` | `yaml\|json` | `yaml` | Output format |

```bash
bagels schema model record
bagels schema model record --format json
```

---

## QUERY COMMANDS

All query commands support `--format/-f (table|json|yaml)`. **Always use `--format yaml` or `--format json`** for machine-readable output.

### Summary

**`bagels summary`** — Summarize income, expenses, and net savings for a month.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--month` | `-m` | `YYYY-MM` | current month | Month to summarize |
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

**Output fields:** month, total_income, total_expenses, net_savings, record_count.

```bash
bagels summary --month 2026-03 --format yaml
```

### Records List

**`bagels records list`** — List expense/income records with optional filters.

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

**Note:** Only non-transfer records returned. Results ordered by date descending.

```bash
bagels records list --month 2026-03 --format yaml
bagels records list --category food --limit 20 --format json
bagels records list --date-from 2026-01-01 --date-to 2026-03-31 --all --format json
```

### Records Show

**`bagels records show RECORD_ID`** — Show details of a single record by ID or slug.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `RECORD_ID` | positional string | required | Integer ID or slug (e.g., `r_2026-03-14_001`) |
| `--format` / `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels records show r_2026-03-14_001 --format yaml
bagels records show 42 --format json
```

### Accounts List

**`bagels accounts list`** — List all visible accounts. Hidden accounts are excluded.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels accounts list --format yaml
```

### Categories Tree

**`bagels categories tree`** — Output the full category tree.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

**Output fields:** id, name, nature, color, depth, parent_id.

```bash
bagels categories tree --format yaml
```

### Spending by Category

**`bagels spending by-category`** — Break down spending totals by category for a month.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--month` | `-m` | `YYYY-MM` | current month | Month to analyze |
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

**Output fields:** month, total, categories [{category, amount, percentage}].

```bash
bagels spending by-category --month 2026-03 --format yaml
```

### Spending by Day

**`bagels spending by-day`** — Break down daily spending totals for a month.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--month` | `-m` | `YYYY-MM` | current month | Month to analyze |
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

**Output fields:** month, total, daily_average, days [{date, amount}].

```bash
bagels spending by-day --month 2026-03 --format yaml
```

### Trends

**`bagels trends`** — Compare monthly financial trends over multiple months.

**Note:** `--months` (plural, int 1-12) means "how many months of history" — NOT the same as `--month YYYY-MM` on other commands.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--months` | `-m` | int (1–12) | `3` | Number of months of history |
| `--category` | `-c` | string | — | Filter to a specific category name |
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

**Output (no --category):** [{month, total_income, total_expenses, net_savings, change_percentage, change_direction}]

**Output (with --category):** [{month, amount}]

```bash
bagels trends --months 6 --format yaml
bagels trends --months 3 --category food --format json
```

---

## MUTATION COMMANDS

With context gathered AND schema inspected, perform mutations. Always provide all required flags to avoid interactive prompts.

### ⚠️ STEP 0: GATHER CONTEXT FIRST ⚠️
**CRITICAL: BEFORE writing any mutation commands:**

1. **Run** `bagels llm context` to get valid account IDs, category slugs, and current state
2. **Run** `bagels schema model record` if creating records via YAML to verify field names
3. **Run** `bagels accounts list --format yaml` and `bagels categories tree --format yaml` to get valid slugs
4. **Provide all required flags** to prevent interactive prompts

**Avoid:**
- ❌ Guessing account IDs or category IDs without checking first
- ❌ Omitting required fields (triggers interactive prompts)
- ❌ Using `--force` on deletes without confirming with the user first

**Follow these practices:**
- ✅ Always gather context before mutations
- ✅ Use slugs from `accounts list` and `categories tree` in YAML batch imports
- ✅ Validate YAML structure before calling `records add --yaml`
- ✅ Use `--format yaml` or `--format json` on create/update commands to confirm results

---

### Records Add (Inline)

**`bagels records add`** — Add a single record using inline flags.

| Flag | Type | Description |
|------|------|-------------|
| `--label` | string | Record label/description |
| `--amount` | float | Amount (must be > 0) |
| `--date` | `YYYY-MM-DD` | Record date (defaults to today) |
| `--account-id` | int | Account ID |
| `--category-id` | int | Category ID (optional) |
| `--person-id` | int | Person ID (optional) |
| `--income` | flag | Mark as income record |
| `--transfer` | flag | Mark as transfer |
| `--transfer-to-account-id` | int | Destination account ID for transfers |
| `--split` | str (repeatable) | Add split as person_slug:amount (e.g. --split alice:30) |
| `--format` / `-f` | `table\|json\|yaml` | Output format (default: table) |

```bash
bagels records add --label "Lunch" --amount 245 --date 2026-03-22 --account-id 1
bagels records add --label "Salary" --amount 50000 --account-id 1 --income
# Add a record with splits
bagels records add --label "Dinner" --amount 100 --account-id 1 --date 2026-03-27 --split alice:30 --split bob:20
```

### Records Add (Batch YAML)

**`bagels records add --yaml PATH`** — Import one or more records from a YAML file.

**Accepted YAML formats:**
- List of dicts: `[{label, amount, date, ...}, ...]`
- Dict with `records` key: `{records: [...]}`
- Dict keyed by slugs: `{r_2026-03-14_001: {...}, ...}`

**Required fields per record:** `label` (string), `amount` (float), `date` (YYYY-MM-DD)

**Optional fields per record:** `accountSlug` (string), `categorySlug` (string), `personSlug` (string), `isIncome` (bool, default false), `isTransfer` (bool, default false)

**WARNING:** May prompt interactively if records fail validation. Pre-validate YAML structure before calling.

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

### Records Update

**`bagels records update IDENTIFIER`** — Update an existing record by integer ID or slug.

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

### Records Delete

**`bagels records delete IDENTIFIER`** — Hard-delete a record by integer ID or slug.

| Argument/Flag | Type | Default | Description |
|---------------|------|---------|-------------|
| `IDENTIFIER` | positional string | required | Integer ID or slug |
| `--force` | flag | — | Skip confirmation prompt |

```bash
bagels records delete 42 --force
bagels records delete r_2026-03-22_001
```

---

## ENTITY CRUD COMMANDS

These follow a consistent pattern: `bagels <entity> (list|show|add|update|delete)`.

### Accounts

**`bagels accounts add`** — Create a new account.

| Flag | Type | Description |
|------|------|-------------|
| `--name` | string | Account name |
| `--balance` | float | Beginning balance |
| `--description` | string | Account description (optional) |
| `--hidden` | flag | Mark account as hidden |
| `--format` / `-f` | `table\|json\|yaml` | Output format |

```bash
bagels accounts add --name "Savings" --balance 10000
```

**`bagels accounts show IDENTIFIER`** — Show details for a single account.

```bash
bagels accounts show 1 --format json
bagels accounts show acc_savings
```

**`bagels accounts update IDENTIFIER`** — Update an existing account.

| Argument/Flag | Type | Description |
|---------------|------|-------------|
| `IDENTIFIER` | positional string | Integer ID or slug |
| `--name` | string | New account name |
| `--balance` | float | New beginning balance |
| `--description` | string | New account description |
| `--hidden/--no-hidden` | flag | Set account visibility |
| `--format` / `-f` | `table\|json\|yaml` | Output format |

```bash
bagels accounts update 1 --name "New Savings"
```

**`bagels accounts delete IDENTIFIER`** — Soft-delete an account.

**Note:** `--cascade` soft-deletes all linked records. Without `--cascade`, delete is blocked if linked records exist.

| Argument/Flag | Type | Description |
|---------------|------|-------------|
| `IDENTIFIER` | positional string | Integer ID or slug |
| `--force` | flag | Skip confirmation prompt |
| `--cascade` | flag | Soft-delete all linked records |

```bash
bagels accounts delete 1 --force
bagels accounts delete 1 --cascade --force
```

### Categories

**`bagels categories list`** — List all categories.

```bash
bagels categories list --format yaml
```

**`bagels categories show IDENTIFIER`** — Show details for a single category.

```bash
bagels categories show 5 --format json
```

**`bagels categories add`** — Create a new category.

| Flag | Type | Description |
|------|------|-------------|
| `--name` | string | Category name |
| `--nature` | `Want\|Need\|Must` | Category nature |
| `--color` | string | Hex color (e.g., `#FF5733`) |
| `--parent-id` | int | Parent category ID (optional) |
| `--format` / `-f` | `table\|json\|yaml` | Output format |

```bash
bagels categories add --name "Dining Out" --nature Need --parent-id 5
bagels categories add --name "Salary" --nature Must
```

**`bagels categories update IDENTIFIER`** — Update an existing category.

| Argument/Flag | Type | Description |
|---------------|------|-------------|
| `IDENTIFIER` | positional string | Integer ID or slug |
| `--name` | string | New category name |
| `--nature` | `Want\|Need\|Must` | New category nature |
| `--color` | string | New hex color |
| `--parent-id` | int | New parent category ID |
| `--format` / `-f` | `table\|json\|yaml` | Output format |

```bash
bagels categories update 5 --name "Food & Dining"
```

**`bagels categories delete IDENTIFIER`** — Delete a category.

**Note:** `--cascade` soft-deletes linked records. Subcategories are NOT automatically deleted.

```bash
bagels categories delete 5 --force
bagels categories delete 5 --cascade
```

### Persons

**`bagels persons list`** — List all persons.

```bash
bagels persons list --format yaml
```

**`bagels persons add`** — Create a new person.

```bash
bagels persons add --name "Alice"
```

**`bagels persons show IDENTIFIER`** — Show details for a single person.

```bash
bagels persons show 1 --format json
```

**`bagels persons update IDENTIFIER`** — Update an existing person.

```bash
bagels persons update 1 --name "Bob"
```

**`bagels persons delete IDENTIFIER`** — Delete a person. `--cascade` soft-deletes linked records (via splits).

```bash
bagels persons delete 1 --force
bagels persons delete 1 --cascade
```

### Templates

**`bagels templates list`** — List all record templates.

```bash
bagels templates list --format yaml
```

**`bagels templates add`** — Create a new record template.

| Flag | Type | Description |
|------|------|-------------|
| `--label` | string | Template label |
| `--amount` | float | Template amount |
| `--account-id` | int | Account ID |
| `--category-id` | int | Category ID (optional) |
| `--income` | flag | Mark as income |
| `--transfer` | flag | Mark as transfer |
| `--transfer-to-account-id` | int | Transfer target account ID |
| `--format` / `-f` | `table\|json\|yaml` | Output format |

```bash
bagels templates add --label "Rent" --amount 15000 --account-id 1
bagels templates add --label "Salary" --amount 50000 --account-id 1 --income
```

**`bagels templates show IDENTIFIER`** — Show details for a single template.

```bash
bagels templates show 1 --format json
```

**`bagels templates update IDENTIFIER`** — Update an existing record template.

| Argument/Flag | Type | Description |
|---------------|------|-------------|
| `IDENTIFIER` | positional string | Integer ID or slug |
| `--label` | string | New template label |
| `--amount` | float | New amount |
| `--account-id` | int | New account ID |
| `--category-id` | int | New category ID |
| `--income/--no-income` | flag | Set income flag |
| `--transfer/--no-transfer` | flag | Set transfer flag |
| `--transfer-to-account-id` | int | New transfer target account ID |
| `--format` / `-f` | `table\|json\|yaml` | Output format |

```bash
bagels templates update 1 --amount 16000
```

**`bagels templates delete IDENTIFIER`** — Hard-delete a record template.

```bash
bagels templates delete 1 --force
```

### Splits

Manage expense splits on records. Splits track shared expenses — who owes what portion of a record.

#### `bagels splits add RECORD_ID`

Add a split to an existing record.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--person` | `-p` | str | required | Person slug or integer ID |
| `--amount` | `-a` | float | required | Split amount |
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels splits add r_2026-03-27_001 --person alice --amount 30
bagels splits add 42 -p bob -a 20
```

#### `bagels splits list RECORD_ID`

List all splits for a record.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--format` | `-f` | `table\|json\|yaml` | `table` | Output format |

```bash
bagels splits list r_2026-03-27_001
```

#### `bagels splits mark-paid SPLIT_ID`

Mark a split as paid (sets isPaid=True, paidDate=today).

```bash
bagels splits mark-paid 5
```

#### `bagels splits delete SPLIT_ID`

Delete a split. Shows confirmation prompt; use `--force` to skip.

| Flag | Short | Type | Default | Description |
|------|-------|------|---------|-------------|
| `--force` | — | flag | false | Skip confirmation prompt |

```bash
bagels splits delete 5
bagels splits delete 5 --force
```

---

## UTILITY COMMANDS

**`bagels init`** — Initialize config, data directory, and SQLite database.

```bash
bagels init
bagels --at ./my-instance init
```

**`bagels locate (config|database)`** — Print the path to the config or database file.

```bash
bagels locate config
bagels locate database
```

---

## WORKFLOW PATTERNS

### 1. Monthly Financial Snapshot

**When:** Get a complete picture of one month's finances in one call.

```bash
bagels llm context --month 2026-03
```

### 2. Spending Analysis

**When:** Analyze spending patterns with detailed records and category breakdown.

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

### 4. Add Records from LLM (Batch YAML)

**When:** Create expense records from natural language user intent.

```bash
# 1. Get valid slugs
bagels accounts list --format yaml
bagels categories tree --format yaml

# 2. Write YAML file
cat > /tmp/new-record.yaml << 'EOF'
- label: "Lunch at MBK"
  amount: 245.00
  date: "2026-03-22"
  accountSlug: "kasikorn-checking"
  categorySlug: "food-dining-out"
  isIncome: false
EOF

# 3. Import
bagels records add --yaml /tmp/new-record.yaml
```

### 5. Quick Single Record from CLI Flags

**When:** Quickly add a single expense/income without a YAML file.

```bash
bagels accounts list --format yaml    # get account IDs
bagels categories tree --format yaml  # get category IDs
bagels records add --label "Coffee" --amount 120 --date 2026-03-22 --account-id 1 --category-id 3
```

### 6. Expense Splitting

**When:** Track shared expenses with multiple people owing portions of a record.

```bash
# 1. Create a shared expense with splits
bagels records add --label "Group dinner" --amount 100 --account-id 1 --split alice:30 --split bob:20

# 2. View splits on a record
bagels splits list r_2026-03-27_001

# 3. Mark a split as paid when someone pays you back
bagels splits mark-paid 5

# 4. Add a split to an existing record
bagels splits add r_2026-03-27_001 --person charlie --amount 15

# 5. Remove a split
bagels splits delete 6 --force
```

---

## THE OPERATIONAL PROCESS

**User request** → **Gather context** → **Perform action**

Each request follows this pattern:

1. **Interpret the user's intent** — What financial operation is being requested?
2. **Gather context** (`bagels llm context`) — Get the current financial state, valid IDs, and slugs
3. **Inspect schema if needed** (`bagels schema model record`) — Verify field names before mutations
4. **Execute the operation** — Run the appropriate query or mutation commands
5. **Confirm results** — Use `--format yaml` on mutations to verify the outcome

**The constants:**
- Always gather context first
- Always use `--format yaml` or `--format json` for machine-readable output
- Always provide all required flags to avoid interactive prompts
- The `--at` flag goes **before** the subcommand

**Key behaviors:**
- `IDENTIFIER` in CRUD commands accepts either integer ID or slug string
- All create/update commands support `--format` for output format
- Delete commands prompt for confirmation by default; use `--force` to skip
- `--cascade` on entity deletes also removes linked records (soft-delete)
- Record deletes are hard deletes (permanent)
- Templates deletes are also hard deletes
