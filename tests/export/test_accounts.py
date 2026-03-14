"""
Tests for account export to YAML format (TDD - RED phase).

These tests define the expected behavior for exporting Account entities
from SQLite to human-readable YAML files with slug-based IDs.
"""

import pytest
from pathlib import Path
from datetime import datetime
import yaml

from bagels.models.account import Account


class TestAccountExport:
    """Test suite for account export functionality."""

    def test_export_single_account_to_yaml(self, in_memory_db, temp_directory):
        """
        Test exporting a single account to YAML file.

        Given: Account with name="Savings", description="Emergency fund",
               beginningBalance=1000.0
        When: export_account_to_yaml(account, temp_dir)
        Then: File exists at temp_dir/accounts.yaml
        And: YAML contains dict keyed by account slug
        And: All fields exported (name, description, beginningBalance,
             createdAt, updatedAt)
        And: Amounts exported as floats with proper precision
        """
        # Arrange
        account = Account(
            name="Savings",
            description="Emergency fund",
            beginningBalance=1000.0,
            repaymentDate=None,
            hidden=False
        )
        in_memory_db.add(account)
        in_memory_db.commit()

        # Act & Assert
        # This function doesn't exist yet - RED phase
        from bagels.export.exporter import export_account_to_yaml

        result_path = export_account_to_yaml(account, temp_directory)

        # Verify file exists
        assert result_path == temp_directory / "accounts.yaml"
        assert result_path.exists()

        # Verify YAML structure
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        assert "accounts" in data
        assert len(data["accounts"]) == 1

        # Account should be keyed by generated slug (acc_ID format)
        account_slug = f"acc_{account.id}"
        assert account_slug in data["accounts"]

        exported_account = data["accounts"][account_slug]
        assert exported_account["name"] == "Savings"
        assert exported_account["description"] == "Emergency fund"
        assert exported_account["beginningBalance"] == 1000.0
        assert exported_account["hidden"] is False
        assert exported_account["repaymentDate"] is None
        assert "createdAt" in exported_account
        assert "updatedAt" in exported_account

    def test_export_multiple_accounts_to_yaml(self, in_memory_db, temp_directory):
        """
        Test exporting multiple accounts to YAML file.

        Given: 3 accounts in database
        When: export_all_accounts(session, temp_dir)
        Then: YAML contains all 3 accounts
        And: Account slugs are keys in dict
        And: No integer IDs exposed (only slugs)
        """
        # Arrange
        account1 = Account(
            name="Savings",
            description="Emergency fund",
            beginningBalance=1000.0,
            hidden=False
        )
        account2 = Account(
            name="Checking",
            description="Daily expenses",
            beginningBalance=2500.0,
            hidden=False
        )
        account3 = Account(
            name="Credit Card",
            description="Visa card",
            beginningBalance=0.0,
            repaymentDate=15,
            hidden=False
        )

        in_memory_db.add_all([account1, account2, account3])
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_all_accounts

        result_path = export_all_accounts(in_memory_db, temp_directory)

        # Verify file exists
        assert result_path == temp_directory / "accounts.yaml"
        assert result_path.exists()

        # Verify YAML structure
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        assert "accounts" in data
        assert len(data["accounts"]) == 3

        # Verify all accounts present with generated slug keys
        for account in [account1, account2, account3]:
            account_slug = f"acc_{account.id}"
            assert account_slug in data["accounts"]
            exported = data["accounts"][account_slug]
            assert exported["name"] == account.name
            assert "id" not in exported  # No integer IDs
            assert "accountId" not in exported

    def test_export_includes_metadata_timestamps(self, in_memory_db, temp_directory):
        """
        Test exporting account with createdAt and updatedAt timestamps.

        Given: Account with createdAt and updatedAt timestamps
        When: Exported to YAML
        Then: Timestamps in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
        And: Timestamps match database values
        """
        # Arrange
        test_time = datetime(2026, 3, 14, 10, 30, 0)
        account = Account(
            name="Test Account",
            description="Metadata test",
            beginningBalance=500.0,
            createdAt=test_time,
            updatedAt=test_time,
            hidden=False
        )
        in_memory_db.add(account)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_account_to_yaml

        result_path = export_account_to_yaml(account, temp_directory)

        # Verify timestamps
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        account_slug = f"acc_{account.id}"
        exported = data["accounts"][account_slug]
        assert exported["createdAt"] == "2026-03-14T10:30:00"
        assert exported["updatedAt"] == "2026-03-14T10:30:00"

    def test_export_handles_null_fields(self, in_memory_db, temp_directory):
        """
        Test exporting account with null/optional fields.

        Given: Account with description=None, repaymentDate=None
        When: Exported to YAML
        Then: Null fields represented as null in YAML
        And: No empty strings or "None" strings
        """
        # Arrange
        account = Account(
            name="Minimal Account",
            description=None,
            beginningBalance=100.0,
            repaymentDate=None,
            hidden=False
        )
        in_memory_db.add(account)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_account_to_yaml

        result_path = export_account_to_yaml(account, temp_directory)

        # Verify null fields
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        account_slug = f"acc_{account.id}"
        exported = data["accounts"][account_slug]
        assert exported["description"] is None
        assert exported["repaymentDate"] is None
        # Verify not string representations
        assert exported["description"] != "None"
        assert exported["description"] != ""

    def test_export_preserves_float_precision(self, in_memory_db, temp_directory):
        """
        Test that monetary values maintain proper float precision.

        Given: Account with beginningBalance=1234.56
        When: Exported to YAML
        Then: Amount exported as float with proper precision
        And: Value matches CONFIG.defaults.round_decimals
        """
        # Arrange
        account = Account(
            name="Precision Test",
            description="Testing float precision",
            beginningBalance=1234.56,
            hidden=False
        )
        in_memory_db.add(account)
        in_memory_db.commit()

        # Act & Assert
        from bagels.export.exporter import export_account_to_yaml

        result_path = export_account_to_yaml(account, temp_directory)

        # Verify precision
        with open(result_path, 'r') as f:
            data = yaml.safe_load(f)

        account_slug = f"acc_{account.id}"
        exported = data["accounts"][account_slug]
        assert isinstance(exported["beginningBalance"], float)
        assert exported["beginningBalance"] == 1234.56
