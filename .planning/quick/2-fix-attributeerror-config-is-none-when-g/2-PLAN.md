---
phase: quick
plan: 2
type: execute
wave: 1
depends_on: []
files_modified:
  - src/bagels/managers/accounts.py
  - src/bagels/managers/utils.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Running `uv run bagels --at './instance/'` starts without AttributeError"
    - "get_account_balance returns a rounded value using CONFIG.defaults.round_decimals"
    - "Period figures and week calculations respect CONFIG defaults"
  artifacts:
    - path: "src/bagels/managers/accounts.py"
      provides: "Lazy CONFIG access via bagels.config module reference"
    - path: "src/bagels/managers/utils.py"
      provides: "Lazy CONFIG access via bagels.config module reference"
  key_links:
    - from: "src/bagels/managers/accounts.py"
      to: "bagels.config.CONFIG"
      via: "import bagels.config as config_mod; config_mod.CONFIG at call time"
      pattern: "config_mod\\.CONFIG"
    - from: "src/bagels/managers/utils.py"
      to: "bagels.config.CONFIG"
      via: "import bagels.config as config_mod; config_mod.CONFIG at call time"
      pattern: "config_mod\\.CONFIG"
---

<objective>
Fix AttributeError where CONFIG is None when get_account_balance (and related functions) are called during RecordTemplateForm initialization when `--at` flag is used.

Purpose: The `--at` flag causes `set_custom_root` to run before `load_config()`. Since `accounts.py` and `utils.py` do `from bagels.config import CONFIG` at module-level, they capture `CONFIG = None` as a fixed binding. All other managers already use the lazy `import bagels.config as config_mod` pattern to access `config_mod.CONFIG` at call time. Apply that same pattern to the two remaining offenders.

Output: accounts.py and utils.py use module-level lazy CONFIG access; no more AttributeError on startup with --at.
</objective>

<execution_context>
@/Users/thepbordin/.claude/get-shit-done/workflows/execute-plan.md
@/Users/thepbordin/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix lazy CONFIG access in accounts.py and utils.py</name>
  <files>src/bagels/managers/accounts.py, src/bagels/managers/utils.py</files>
  <action>
In BOTH files, replace the module-level static import with a lazy module reference:

BEFORE (both files, line 8):
```python
from bagels.config import CONFIG
```

AFTER (both files):
```python
import bagels.config as config_mod
```

Then update every bare `CONFIG` reference in each file to `config_mod.CONFIG`.

For src/bagels/managers/accounts.py:
- Line 140: `return round(balance, CONFIG.defaults.round_decimals)` → `return round(balance, config_mod.CONFIG.defaults.round_decimals)`
- The `_trigger_entity_export` function at lines 25-42 already uses `config_mod` correctly — do NOT change those lines, only replace the top-level `from bagels.config import CONFIG` import.

For src/bagels/managers/utils.py:
- Line 59: `first_day_of_week = CONFIG.defaults.first_day_of_week` → `first_day_of_week = config_mod.CONFIG.defaults.first_day_of_week`
- Line 167: `return abs(round(total, CONFIG.defaults.round_decimals))` → `return abs(round(total, config_mod.CONFIG.defaults.round_decimals))`
- Line 185: `return round(net / days, CONFIG.defaults.round_decimals)` → `return round(net / days, config_mod.CONFIG.defaults.round_decimals)`
- Lines 215-217: three `CONFIG.state.budgeting.*` accesses → `config_mod.CONFIG.state.budgeting.*`

Do not change any function signatures, logic, or other imports.
  </action>
  <verify>
    <automated>cd /Users/thepbordin/Developer/Bagels && python -c "import bagels.managers.accounts; import bagels.managers.utils; print('imports OK')"</automated>
  </verify>
  <done>Both files import via `import bagels.config as config_mod`; all bare `CONFIG` references replaced with `config_mod.CONFIG`; no AttributeError on import or when functions are called after load_config() runs.</done>
</task>

<task type="auto">
  <name>Task 2: Smoke test --at flag startup</name>
  <files></files>
  <action>
Verify the fix works end-to-end. Create a minimal test that:
1. Sets a custom root path (simulating --at)
2. Calls load_config()
3. Calls get_account_balance or get_all_accounts_with_balance

If a real instance directory is not available, verify by importing the module and confirming CONFIG access works after load_config() is called.

Run: `python -c "from bagels.config import load_config; load_config(); from bagels.managers.accounts import get_account_balance; print('No AttributeError — fix confirmed')"`
  </action>
  <verify>
    <automated>cd /Users/thepbordin/Developer/Bagels && python -c "from bagels.config import load_config; load_config(); from bagels.managers.accounts import get_account_balance; print('OK')"</automated>
  </verify>
  <done>Script exits 0 with "OK" printed; no AttributeError from CONFIG being None.</done>
</task>

</tasks>

<verification>
- `python -c "import bagels.managers.accounts"` exits 0
- `python -c "import bagels.managers.utils"` exits 0
- After `load_config()`, calling account balance functions does not raise AttributeError
- `grep "from bagels.config import CONFIG" src/bagels/managers/accounts.py src/bagels/managers/utils.py` returns no results
- `grep "config_mod.CONFIG" src/bagels/managers/accounts.py src/bagels/managers/utils.py` returns matches for every former `CONFIG` usage site
</verification>

<success_criteria>
- No `AttributeError: 'NoneType' object has no attribute 'defaults'` when running `uv run bagels --at "./instance/"`
- Both accounts.py and utils.py use `config_mod.CONFIG` (lazy) not the stale `from bagels.config import CONFIG` (eager)
- All existing tests continue to pass
</success_criteria>

<output>
After completion, create `.planning/quick/2-fix-attributeerror-config-is-none-when-g/2-SUMMARY.md`
</output>
