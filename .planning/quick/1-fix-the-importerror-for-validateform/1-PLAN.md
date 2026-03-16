---
phase: quick-fix
plan: 1
type: execute
wave: 1
depends_on: []
files_modified: [src/bagels/utils/validation.py]
autonomous: true
requirements: []
user_setup: []
must_haves:
  truths:
    - "validateForm function is available in bagels.utils.validation module"
    - "Modal components can import and use validateForm without ImportError"
    - "Form validation works for all field types (integer, number, date, autocomplete, etc.)"
  artifacts:
    - path: "src/bagels/utils/validation.py"
      provides: "Form validation function for TUI modals"
      exports: ["validateForm"]
  key_links:
    - from: "src/bagels/modals/record.py"
      to: "src/bagels/utils/validation.py"
      via: "import validateForm"
      pattern: "from bagels.utils.validation import validateForm"
    - from: "src/bagels/modals/transfer.py"
      to: "src/bagels/utils/validation.py"
      via: "import validateForm"
      pattern: "from bagels.utils.validation import validateForm"
    - from: "src/bagels/modals/input.py"
      to: "src/bagels/utils/validation.py"
      via: "import validateForm"
      pattern: "from bagels.utils.validation import validateForm"
---

<objective>
Restore the missing validateForm function to fix ImportError in modal components

Purpose: The validateForm function was accidentally removed during refactoring (commit 0aff1a7a) when validation.py was rewritten to only export YAML validation functions. This broke all modal components that depend on form validation.

Output: Working validateForm function restored in validation.py, all modals can import and use it
</objective>

<execution_context>
@/Users/thepbordin/.claude/get-shit-done/workflows/execute-plan.md
@/Users/thepbordin/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md

# Original validateForm function (from git history)
```python
def validateForm(
    formComponent: Widget, formData: Form
) -> Tuple[Dict[str, Any], Dict[str, str], bool]:
    result = {}
    errors = {}
    isValid = True

    for field in formData.fields:
        fieldKey = field.key
        fieldWidget = formComponent.query_one(f"#field-{fieldKey}")
        fieldValue = (
            fieldWidget.heldValue
            if hasattr(fieldWidget, "heldValue")
            else fieldWidget.value
        )

        error = None

        match field.type:
            case "integer":
                is_valid, error, num_val = _validate_number(fieldValue, field)
                if is_valid and fieldValue is not None and num_val is not None:
                    result[fieldKey] = num_val

            case "number":
                is_valid, error, num_val = _validate_number(
                    fieldValue, field, is_float=True
                )
                if is_valid and fieldValue is not None and num_val is not None:
                    result[fieldKey] = num_val

            case "date":
                date, error = _validate_date(fieldValue, field)
                if date:
                    result[fieldKey] = date

            case "dateAutoDay":
                date, error = _validate_date(fieldValue, field, auto_day=True)
                if date:
                    result[fieldKey] = date

            case "autocomplete":
                if field.autocomplete_selector:
                    is_valid, error = _validate_autocomplete(
                        fieldWidget.value, fieldValue, field
                    )
                    if is_valid and fieldValue:
                        result[fieldKey] = fieldValue
                else:
                    if not fieldWidget.value and field.is_required:
                        error = "Required"
                    else:
                        result[fieldKey] = fieldWidget.value

            case _:
                if not fieldValue and field.is_required:
                    error = "Required"
                else:
                    result[fieldKey] = fieldValue

        if error:
            errors[fieldKey] = error
            isValid = False

    return result, errors, isValid
```

# Helper functions (from git history)
```python
def _validate_number(
    value: str, field: FormField, is_float: bool = False
) -> Tuple[bool, str | None]:
    """Validate a number field and return (is_valid, error_message)"""
    # ... (implementation details)

def _validate_date(
    value: str, field: FormField, auto_day: bool = False
) -> Tuple[datetime | None, str | None]:
    """Validate a date field and return (parsed_date, error_message)"""
    # ... (implementation details)

def _validate_autocomplete(
    value: str, held_value: str, field: FormField
) -> Tuple[bool, str | None]:
    """Validate an autocomplete field and return (is_valid, error_message)"""
    # ... (implementation details)
```
</context>

<tasks>

<task type="auto">
  <name>Task 1: Restore validateForm function and helpers to validation.py</name>
  <files>src/bagels/utils/validation.py</files>
  <action>
Add the missing validateForm function and its helper functions back to src/bagels/utils/validation.py.

The file currently only re-exports YAML validation functions. You need to:
1. Keep the existing YAML validation re-exports (for backward compatibility)
2. Add back the form validation functions: validateForm, _validate_number, _validate_date, _validate_autocomplete
3. Import required dependencies: datetime, Tuple, Dict, Any from typing; Widget from textual.widget; Form, FormField from bagels.forms.form; parse_formula_expression from bagels.utils.format

Use the exact implementation from git history (commit 0aff1a7a^) to ensure compatibility with existing modal code.

IMPORTANT: Do NOT remove the YAML validation re-exports - they are needed for tests.
  </action>
  <verify>
    <automated>python -c "from bagels.utils.validation import validateForm; print('validateForm imported successfully')"</automated>
  </verify>
  <done>
    - validateForm function can be imported from bagels.utils.validation
    - All three modal files (record.py, transfer.py, input.py) can import validateForm without ImportError
    - YAML validation functions are still available (tests still work)
  </done>
</task>

</tasks>

<verification>
- Python can import validateForm from bagels.utils.validation
- No ImportError when running modal components
- YAML validation functions still work (backward compatibility maintained)
</verification>

<success_criteria>
- validateForm function restored in src/bagels/utils/validation.py
- Helper functions (_validate_number, _validate_date, _validate_autocomplete) restored
- All imports in modal components resolve successfully
- YAML validation exports still work
</success_criteria>

<output>
After completion, create `.planning/quick/1-fix-the-importerror-for-validateform/1-SUMMARY.md`
</output>
