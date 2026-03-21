"""
YAML validation tests for import functionality.

Tests cover validation logic for all entity types before import:
- Required field validation
- Foreign key reference validation
- Data type validation (timestamps, monetary values)
- Slug format validation
- Comprehensive error reporting (not fail-fast)

Requirements: FMT-01, FMT-02, FMT-03, FMT-05
"""

import pytest
from datetime import datetime
from pathlib import Path


class TestAccountsValidation:
    """Test validation for accounts YAML data."""

    def test_validate_accounts_yaml_structure(self, in_memory_db):
        """
        Test that valid accounts YAML passes validation.

        Given: Valid accounts YAML with dict structure
        When: validate_accounts_yaml(yaml_data)
        Then: Returns (True, [])
        And: No validation errors
        """
        from bagels.utils.validation import validate_accounts_yaml

        yaml_data = {
            "acc_savings": {
                "name": "Savings",
                "description": "Emergency fund",
                "beginningBalance": 1000.0,
                "repaymentDate": None,
                "hidden": False,
                "createdAt": "2026-03-14T10:30:00",
                "updatedAt": "2026-03-14T10:30:00",
            }
        }

        is_valid, errors = validate_accounts_yaml(yaml_data)

        assert is_valid is True
        assert errors == []

    def test_detect_missing_required_fields(self, in_memory_db):
        """
        Test that missing required fields are detected.

        Given: Accounts YAML missing 'name' field
        When: validate_accounts_yaml(yaml_data)
        Then: Returns (False, [error_list])
        And: Error specifies "Missing required field 'name'"
        """
        from bagels.utils.validation import validate_accounts_yaml

        yaml_data = {
            "acc_savings": {
                "description": "Emergency fund",
                "beginningBalance": 1000.0,
                "hidden": False,
            }
        }

        is_valid, errors = validate_accounts_yaml(yaml_data)

        assert is_valid is False
        assert len(errors) > 0
        assert any("name" in str(error).lower() for error in errors)

    def test_validate_timestamp_format(self, in_memory_db):
        """
        Test that invalid timestamp format is detected.

        Given: YAML with invalid timestamp format
        When: validate_accounts_yaml(yaml_data)
        Then: Returns (False, [error_list])
        And: Error specifies "Invalid timestamp format"
        """
        from bagels.utils.validation import validate_accounts_yaml

        yaml_data = {
            "acc_savings": {
                "name": "Savings",
                "description": "Emergency fund",
                "beginningBalance": 1000.0,
                "hidden": False,
                "createdAt": "invalid-timestamp",
                "updatedAt": "2026-03-14T10:30:00",
            }
        }

        is_valid, errors = validate_accounts_yaml(yaml_data)

        assert is_valid is False
        assert any(
            "timestamp" in str(error).lower() or "format" in str(error).lower()
            for error in errors
        )


class TestRecordsValidation:
    """Test validation for records YAML data."""

    def test_detect_broken_foreign_key_references(self, in_memory_db, sample_account):
        """
        Test that broken foreign key references are detected.

        Given: Record YAML with accountSlug pointing to non-existent account
        When: validate_records_yaml(yaml_data, session)
        Then: Returns (False, [error_list])
        And: Error specifies "Referenced account 'acc_missing' does not exist"
        """
        from bagels.utils.validation import validate_records_yaml

        yaml_data = {
            "r_2026-03-14_001": {
                "label": "Test Record",
                "amount": 50.0,
                "date": "2026-03-14T00:00:00",
                "accountSlug": "acc_missing",
                "categorySlug": None,
                "isIncome": False,
                "isTransfer": False,
                "createdAt": "2026-03-14T10:30:00",
                "updatedAt": "2026-03-14T10:30:00",
            }
        }

        is_valid, errors = validate_records_yaml(yaml_data, in_memory_db)

        assert is_valid is False
        assert any(
            "account" in str(error).lower() and "acc_missing" in str(error)
            for error in errors
        )

    def test_validate_monetary_value_format(self, in_memory_db, sample_account):
        """
        Test that invalid monetary value format is detected.

        Given: YAML with amount as string instead of float
        When: validate_records_yaml(yaml_data)
        Then: Returns (False, [error_list])
        And: Error specifies "Amount must be a number"
        """
        from bagels.utils.validation import validate_records_yaml

        yaml_data = {
            "r_2026-03-14_001": {
                "label": "Test Record",
                "amount": "not-a-number",
                "date": "2026-03-14T00:00:00",
                "accountSlug": "acc_savings",
                "categorySlug": None,
                "isIncome": False,
                "isTransfer": False,
                "createdAt": "2026-03-14T10:30:00",
                "updatedAt": "2026-03-14T10:30:00",
            }
        }

        is_valid, errors = validate_records_yaml(yaml_data, in_memory_db)

        assert is_valid is False
        assert any(
            "amount" in str(error).lower() and "number" in str(error).lower()
            for error in errors
        )

    def test_validate_slug_format(self, in_memory_db, sample_account):
        """
        Test that invalid slug format is detected.

        Given: Record YAML with invalid slug format (not r_YYYY-MM-DD_###)
        When: validate_records_yaml(yaml_data)
        Then: Returns (False, [error_list])
        And: Error specifies "Invalid slug format"
        """
        from bagels.utils.validation import validate_records_yaml

        yaml_data = {
            "invalid_slug": {
                "label": "Test Record",
                "amount": 50.0,
                "date": "2026-03-14T00:00:00",
                "accountSlug": "acc_savings",
                "categorySlug": None,
                "isIncome": False,
                "isTransfer": False,
                "createdAt": "2026-03-14T10:30:00",
                "updatedAt": "2026-03-14T10:30:00",
            }
        }

        is_valid, errors = validate_records_yaml(yaml_data, in_memory_db)

        assert is_valid is False
        assert any(
            "slug" in str(error).lower() and "format" in str(error).lower()
            for error in errors
        )


class TestCategoriesValidation:
    """Test validation for categories YAML data."""

    def test_validate_category_structure(self, in_memory_db):
        """
        Test that valid categories YAML passes validation.

        Given: Valid categories YAML with dict structure
        When: validate_categories_yaml(yaml_data)
        Then: Returns (True, [])
        """
        from bagels.utils.validation import validate_categories_yaml

        yaml_data = {
            "cat_groceries": {
                "name": "Groceries",
                "parentSlug": None,
                "nature": "expense",
                "color": "#FF5733",
                "createdAt": "2026-03-14T10:30:00",
                "updatedAt": "2026-03-14T10:30:00",
            }
        }

        is_valid, errors = validate_categories_yaml(yaml_data)

        assert is_valid is True
        assert errors == []

    def test_detect_broken_parent_references(self, in_memory_db):
        """
        Test that broken parent category references are detected.

        Given: Category YAML with parentSlug pointing to non-existent category
        When: validate_categories_yaml(yaml_data, session)
        Then: Returns (False, [error_list])
        """
        from bagels.utils.validation import validate_categories_yaml

        yaml_data = {
            "cat_child": {
                "name": "Child Category",
                "parentSlug": "cat_missing",
                "nature": "expense",
                "color": "#FF5733",
                "createdAt": "2026-03-14T10:30:00",
                "updatedAt": "2026-03-14T10:30:00",
            }
        }

        is_valid, errors = validate_categories_yaml(yaml_data, in_memory_db)

        assert is_valid is False
        assert any(
            "parent" in str(error).lower() or "cat_missing" in str(error)
            for error in errors
        )


class TestPersonsValidation:
    """Test validation for persons YAML data."""

    def test_validate_person_structure(self, in_memory_db):
        """
        Test that valid persons YAML passes validation.

        Given: Valid persons YAML with dict structure
        When: validate_persons_yaml(yaml_data)
        Then: Returns (True, [])
        """
        from bagels.utils.validation import validate_persons_yaml

        yaml_data = {
            "person_john_doe": {
                "name": "John Doe",
                "createdAt": "2026-03-14T10:30:00",
                "updatedAt": "2026-03-14T10:30:00",
            }
        }

        is_valid, errors = validate_persons_yaml(yaml_data)

        assert is_valid is True
        assert errors == []


class TestTemplatesValidation:
    """Test validation for record templates YAML data."""

    def test_validate_template_structure(
        self, in_memory_db, sample_account, sample_category
    ):
        """
        Test that valid templates YAML passes validation.

        Given: Valid templates YAML with dict structure
        When: validate_templates_yaml(yaml_data, session)
        Then: Returns (True, [])
        """
        from bagels.utils.validation import validate_templates_yaml

        yaml_data = {
            "tpl_monthly_rent": {
                "label": "Monthly Rent",
                "amount": 1500.0,
                "accountSlug": "acc_savings_extra",
                "categorySlug": "cat_groceries_extra",
                "personSlug": None,
                "isIncome": False,
                "ordinal": 0,
                "createdAt": "2026-03-14T10:30:00",
                "updatedAt": "2026-03-14T10:30:00",
            }
        }

        # First, create the referenced entities
        from bagels.models.account import Account
        from bagels.models.category import Category

        account = Account(
            slug="acc_savings_extra",
            name="Savings Extra",
            beginningBalance=1000.0,
            hidden=False,
        )
        category = Category(
            slug="cat_groceries_extra",
            name="Groceries Extra",
            nature="expense",
            color="#FF5733",
        )
        in_memory_db.add(account)
        in_memory_db.add(category)
        in_memory_db.commit()

        is_valid, errors = validate_templates_yaml(yaml_data, in_memory_db)

        assert is_valid is True
        assert errors == []


class TestValidationErrorReporting:
    """Test comprehensive error reporting (not fail-fast)."""

    def test_validate_all_then_prompt_multiple_errors(self, in_memory_db):
        """
        Test that all validation errors are reported together.

        Given: YAML with multiple validation errors
        When: validate_yaml(yaml_data, entity_type, session)
        Then: Returns (False, [all_errors])
        And: All errors listed together (not fail-fast)
        """
        from bagels.utils.validation import validate_accounts_yaml

        yaml_data = {
            "acc_1": {
                "description": "Missing name",
                "beginningBalance": 1000.0,
                "hidden": False,
            },
            "acc_2": {
                "name": "Account 2",
                "description": "Missing beginningBalance",
                "hidden": False,
            },
            "acc_3": {
                "name": "Account 3",
                "beginningBalance": "not-a-number",
                "hidden": False,
            },
        }

        is_valid, errors = validate_accounts_yaml(yaml_data)

        assert is_valid is False
        # Should have multiple errors (at least 3, one per account)
        assert len(errors) >= 3
