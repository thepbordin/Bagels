---
phase: quick-4
plan: 1
type: execute
wave: 1
depends_on: []
files_modified:
  - src/bagels/components/modules/accountmode.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "AccountMode rebuilds without VisualError when account.description is None"
    - "Accounts with no description render an empty label (not a crash)"
  artifacts:
    - path: src/bagels/components/modules/accountmode.py
      provides: "Fixed description_label.update() call"
      contains: "account.description or \"\""
  key_links:
    - from: "rebuild() in AccountMode"
      to: "Label.update()"
      via: "description_label.update(account.description or \"\")"
      pattern: "description_label\\.update\\(account\\.description or"
---

<objective>
Fix VisualError crash in AccountMode.rebuild() when account.description is None.

Purpose: Textual's Label.update() rejects None — it requires a str or Rich renderable. Accounts without a description (description=None) cause a VisualError on every rebuild cycle.

Output: One-line fix at line 107 of accountmode.py. No behaviour change for accounts that have a description.
</objective>

<execution_context>
@/Users/thepbordin/.claude/get-shit-done/workflows/execute-plan.md
@/Users/thepbordin/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

The same null-guard pattern is already used in AccountsList.__init__ (line 32 of the same file):
  str(account.description or "")

The rebuild() method at line 107 is missing this guard.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Guard account.description in description_label.update()</name>
  <files>src/bagels/components/modules/accountmode.py</files>
  <action>
    On line 107, change:
      description_label.update(account.description)
    to:
      description_label.update(account.description or "")

    This matches the existing pattern on line 32 inside AccountsList.__init__:
      str(account.description or "")
    (str() wrapper is not needed here because "" is already a valid str for Label.update, and the existing None/empty-string class logic on lines 108-111 is unaffected.)

    No other changes required.
  </action>
  <verify>
    <automated>cd /Users/thepbordin/Developer/Bagels && python -c "
import ast, sys
with open('src/bagels/components/modules/accountmode.py') as f:
    src = f.read()
assert 'description_label.update(account.description or \"\")' in src, 'Fix not applied'
ast.parse(src)
print('OK: fix present and file parses cleanly')
"</automated>
  </verify>
  <done>Line 107 reads `description_label.update(account.description or "")`. File parses without errors. No VisualError when account.description is None.</done>
</task>

</tasks>

<verification>
Run the syntax check in the verify block above. Optionally launch the TUI and navigate to an account with no description to confirm it renders without crashing.
</verification>

<success_criteria>
- `description_label.update(account.description or "")` is present at the fix site
- File parses cleanly (no SyntaxError)
- AccountMode.rebuild() no longer raises VisualError for None descriptions
</success_criteria>

<output>
After completion, create `.planning/quick/4-fix-visualerror-account-description-none/4-SUMMARY.md`
</output>
