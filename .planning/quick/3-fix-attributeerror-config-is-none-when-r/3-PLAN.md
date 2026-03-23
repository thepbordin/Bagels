---
phase: quick-03
plan: 3
type: execute
wave: 1
depends_on: []
files_modified:
  - src/bagels/components/modules/records/_table_builder.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "App starts without crashing when records have null category"
    - "Null-category records render with a sensible fallback (grey color, 'No Category' label)"
  artifacts:
    - path: src/bagels/components/modules/records/_table_builder.py
      provides: "Null-safe category access in _format_record_fields and _add_split_rows"
  key_links:
    - from: "_format_record_fields"
      to: "record.category"
      via: "guard check before .color and .name access"
      pattern: "record\\.category is None"
    - from: "_add_split_rows"
      to: "record.category"
      via: "guard check before .color access"
      pattern: "record\\.category is None"
---

<objective>
Guard against null category in _table_builder.py so records without an assigned category don't crash the TUI.

Purpose: The `./instance/` database contains records with null categories. Two methods access `record.category.color` unconditionally — they crash with `AttributeError: 'NoneType' object has no attribute 'color'`.
Output: Null-safe _format_record_fields and _add_split_rows that fall back gracefully.
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
  <name>Task 1: Guard null category in _format_record_fields and _add_split_rows</name>
  <files>src/bagels/components/modules/records/_table_builder.py</files>
  <action>
In `_format_record_fields` (around line 180), the `else` branch (non-transfer records) accesses `record.category.color` and `record.category.name` without checking for None.

Replace the two unsafe lines:
```python
color_tag = record.category.color.lower()
category_string = f"[{color_tag}]{CONFIG.symbols.category_color}[/{color_tag}] {record.category.name}"
```
with a null-safe version:
```python
if record.category is not None:
    color_tag = record.category.color.lower()
    category_string = f"[{color_tag}]{CONFIG.symbols.category_color}[/{color_tag}] {record.category.name}"
else:
    color_tag = "grey"
    category_string = f"[{color_tag}]{CONFIG.symbols.category_color}[/{color_tag}] No Category"
```

In `_add_split_rows` (around line 201), the first line accesses `record.category.color` without guarding:
```python
color = record.category.color.lower()
```
Replace with:
```python
color = record.category.color.lower() if record.category is not None else "grey"
```

Do NOT change any other logic. Do NOT alter import statements or unrelated methods.
  </action>
  <verify>
    <automated>cd /Users/thepbordin/Developer/Bagels && python -c "from bagels.components.modules.records._table_builder import RecordTableBuilder; print('import OK')"</automated>
  </verify>
  <done>Both methods handle None category without raising AttributeError. Import succeeds.</done>
</task>

</tasks>

<verification>
After applying the fix, the app should launch without crashing against the instance DB:
`uv run bagels --at "./instance/"`

The table should display rows with null-category records showing "No Category" in grey instead of crashing.
</verification>

<success_criteria>
- `uv run bagels --at "./instance/"` starts without AttributeError
- Records with null category display "No Category" in grey
- Records with a valid category continue to display correctly
</success_criteria>

<output>
After completion, update `.planning/STATE.md` Quick Tasks Completed table with entry #3.
</output>
