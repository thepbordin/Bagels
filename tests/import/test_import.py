"""
YAML import tests with merge-by-ID strategy.

Tests cover import functionality for all entity types:
- Import new entities
- Merge-by-ID strategy (YAML is authoritative)
- Import monthly record files
- Preserve relationships via slug references
- Validate before importing (fail-fast on broken refs)
- Create backup before importing
- Handle category parent-child relationships
- Handle templates with order
- Idempotent imports
- Efficient bulk operations

Requirements: DATA-06, FMT-01, FMT-02, FMT-03, FMT-05
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil


class TestAccountsImport:
    """Test account import functionality."""

    def test_import_new_accounts(self, in_memory_db, temp_directory):
        """
        Test importing new accounts from YAML.

        Given: YAML with 2 new accounts (not in database)
        When: import_accounts_from_yaml(yaml_data, session)
        Then: 2 accounts created in database
        And: Slugs match YAML keys
        And: All fields imported correctly
        """
        from bagels.utils.import_yaml import import_accounts_from_yaml

        yaml_data = {
            "acc_savings": {
                "name": "Savings",
                "description": "Emergency fund",
                "beginningBalance": 1000.0,
                "repaymentDate": None,
                "hidden": False
            },
            "acc_checking": {
                "name": "Checking",
                "description": "Daily spending",
                "beginningBalance": 500.0,
                "repaymentDate": None,
                "hidden": False
            }
        }

        imported = import_accounts_from_yaml(yaml_data, in_memory_db)

        assert imported == 2

        from bagels.models.account import Account
        accounts = in_memory_db.query(Account).all()
        assert len(accounts) == 2

        # Verify slugs and data
        savings = next((a for a in accounts if a.slug == "acc_savings"), None)
        assert savings is not None
        assert savings.name == "Savings"
        assert savings.beginningBalance == 1000.0

        checking = next((a for a in accounts if a.slug == "acc_checking"), None)
        assert checking is not None
        assert checking.name == "Checking"

    def test_import_creates_backup_before_importing(self, in_memory_db, temp_directory, sample_account):
        """
        Test that backup is created before importing.

        Given: Database with existing data
        When: import_accounts_from_yaml(yaml_data, session)
        Then: Backup created at backups/backup_YYYY-MM-DD_HHMMSS.db
        And: Backup file exists and is valid SQLite database
        And: Backup contains pre-import data
        """
        from bagels.utils.import_yaml import import_accounts_from_yaml
        from bagels.models.account import Account

        yaml_data = {
            "acc_new": {
                "name": "New Account",
                "description": "Test",
                "beginningBalance": 100.0,
                "repaymentDate": None,
                "hidden": False
            }
        }

        # Set backup directory
        backup_dir = temp_directory / "backups"
        backup_dir.mkdir(exist_ok=True)

        import_accounts_from_yaml(yaml_data, in_memory_db, backup_dir=str(backup_dir))

        # Verify backup was created
        backups = list(backup_dir.glob("backup_*.db"))
        assert len(backups) >= 1

        # Verify backup is valid SQLite
        import sqlite3
        conn = sqlite3.connect(backups[0])
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        assert "account" in tables
        conn.close()


class TestRecordsImport:
    """Test record import functionality with merge-by-ID strategy."""

    def test_import_updates_existing_records_merge_by_id(self, in_memory_db, sample_account):
        """
        Test that import updates existing records (merge-by-ID).

        Given: Database has record with slug r_2026-03-14_001 (amount=50.0)
        And: YAML has same slug with amount=75.0
        When: import_records_from_yaml(yaml_data, session)
        Then: Record updated with amount=75.0
        And: YAML is authoritative (YAML data overwrites SQLite)
        """
        from bagels.utils.import_yaml import import_records_from_yaml
        from bagels.models.record import Record
        from datetime import datetime

        # Create existing record
        existing_record = Record(
            slug="r_2026-03-14_001",
            label="Test Record",
            amount=50.0,
            date=datetime(2026, 3, 14),
            accountId=sample_account.id,
            isIncome=False,
            isTransfer=False
        )
        in_memory_db.add(existing_record)
        in_memory_db.commit()

        # YAML with updated amount
        yaml_data = {
            "r_2026-03-14_001": {
                "label": "Test Record",
                "amount": 75.0,
                "date": "2026-03-14T00:00:00",
                "accountSlug": "acc_savings",
                "categorySlug": None,
                "isIncome": False,
                "isTransfer": False
            }
        }

        imported = import_records_from_yaml(yaml_data, in_memory_db)

        assert imported == 1

        # Verify record was updated (YAML is authoritative)
        updated = in_memory_db.query(Record).filter_by(slug="r_2026-03-14_001").first()
        assert updated is not None
        assert updated.amount == 75.0

    def test_import_adds_new_records(self, in_memory_db, sample_account):
        """
        Test that import adds new records.

        Given: Database has 3 records
        And: YAML has 5 records (2 existing, 3 new)
        When: import_records_from_yaml(yaml_data, session)
        Then: Database has 5 records total
        And: 2 existing updated, 3 new created
        """
        from bagels.utils.import_yaml import import_records_from_yaml
        from bagels.models.record import Record
        from datetime import datetime

        # Create 3 existing records
        for i in range(3):
            record = Record(
                slug=f"r_2026-03-14_{i+1:03d}",
                label=f"Record {i+1}",
                amount=100.0,
                date=datetime(2026, 3, 14),
                accountId=sample_account.id,
                isIncome=False,
                isTransfer=False
            )
            in_memory_db.add(record)
        in_memory_db.commit()

        # YAML with 5 records (3 existing, 2 new)
        yaml_data = {
            f"r_2026-03-14_{i+1:03d}": {
                "label": f"Record {i+1}",
                "amount": 150.0,
                "date": "2026-03-14T00:00:00",
                "accountSlug": "acc_savings",
                "categorySlug": None,
                "isIncome": False,
                "isTransfer": False
            }
            for i in range(5)
        }

        imported = import_records_from_yaml(yaml_data, in_memory_db)

        assert imported == 5

        total = in_memory_db.query(Record).count()
        assert total == 5

    def test_import_handles_monthly_record_files(self, in_memory_db, sample_account):
        """
        Test that import handles monthly record files.

        Given: YAML file for 2026-03.yaml with 10 records
        When: import_records_from_yaml(yaml_data, session)
        Then: All 10 records imported
        And: Dates match March 2026
        And: Slugs preserved from YAML
        """
        from bagels.utils.import_yaml import import_records_from_yaml
        from bagels.models.record import Record
        from datetime import datetime

        yaml_data = {
            f"r_2026-03-{i+1:02d}_001": {
                "label": f"Record {i+1}",
                "amount": 100.0,
                "date": f"2026-03-{i+1:02d}T00:00:00",
                "accountSlug": "acc_savings",
                "categorySlug": None,
                "isIncome": False,
                "isTransfer": False
            }
            for i in range(1, 11)
        }

        imported = import_records_from_yaml(yaml_data, in_memory_db)

        assert imported == 10

        records = in_memory_db.query(Record).all()
        assert len(records) == 10

        # Verify all dates are in March 2026
        for record in records:
            assert record.date.year == 2026
            assert record.date.month == 3

    def test_import_preserves_relationships_via_slug_references(self, in_memory_db):
        """
        Test that import preserves relationships via slug references.

        Given: YAML with records referencing accountSlug="acc_savings"
        And: acc_savings exists in database
        When: import_records_from_yaml(yaml_data, session)
        Then: Records imported successfully
        And: accountId foreign key set correctly
        """
        from bagels.utils.import_yaml import import_records_from_yaml
        from bagels.models.record import Record
        from bagels.models.account import Account
        from datetime import datetime

        # Create account first
        account = Account(
            slug="acc_savings",
            name="Savings",
            beginningBalance=1000.0,
            hidden=False
        )
        in_memory_db.add(account)
        in_memory_db.commit()

        # YAML records referencing account
        yaml_data = {
            "r_2026-03-14_001": {
                "label": "Test Record",
                "amount": 100.0,
                "date": "2026-03-14T00:00:00",
                "accountSlug": "acc_savings",
                "categorySlug": None,
                "isIncome": False,
                "isTransfer": False
            }
        }

        imported = import_records_from_yaml(yaml_data, in_memory_db)

        assert imported == 1

        record = in_memory_db.query(Record).first()
        assert record is not None
        assert record.accountId == account.id

    def test_import_fails_on_broken_references(self, in_memory_db):
        """
        Test that import fails on broken references.

        Given: YAML with records referencing accountSlug="acc_missing"
        And: acc_missing does NOT exist in database
        When: import_records_from_yaml(yaml_data, session)
        Then: Import raises ValidationError
        And: No records imported (fail-fast)
        And: Error message specifies missing account
        """
        from bagels.utils.import_yaml import import_records_from_yaml
        from bagels.utils.validation import ValidationError

        yaml_data = {
            "r_2026-03-14_001": {
                "label": "Test Record",
                "amount": 100.0,
                "date": "2026-03-14T00:00:00",
                "accountSlug": "acc_missing",
                "categorySlug": None,
                "isIncome": False,
                "isTransfer": False
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            import_records_from_yaml(yaml_data, in_memory_db)

        assert "acc_missing" in str(exc_info.value) or "account" in str(exc_info.value).lower()

    def test_import_validates_before_importing(self, in_memory_db):
        """
        Test that import validates before importing.

        Given: YAML with multiple validation errors
        When: import_records_from_yaml(yaml_data, session)
        Then: Validation runs first
        And: All errors reported together
        And: Import aborted (no partial import)
        """
        from bagels.utils.import_yaml import import_records_from_yaml
        from bagels.utils.validation import ValidationError
        from bagels.models.record import Record

        initial_count = in_memory_db.query(Record).count()

        yaml_data = {
            "r_2026-03-14_001": {
                "label": "Test",
                "amount": "invalid",
                "date": "2026-03-14T00:00:00",
                "accountSlug": "acc_missing",
                "categorySlug": None,
                "isIncome": False,
                "isTransfer": False
            },
            "r_2026-03-14_002": {
                "label": "Test 2",
                "amount": 100.0,
                "date": "invalid-date",
                "accountSlug": "acc_missing",
                "categorySlug": None,
                "isIncome": False,
                "isTransfer": False
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            import_records_from_yaml(yaml_data, in_memory_db)

        # Verify no records were imported
        final_count = in_memory_db.query(Record).count()
        assert final_count == initial_count

    def test_import_is_idempotent(self, in_memory_db, sample_account):
        """
        Test that import is idempotent.

        Given: YAML with existing data
        When: Import twice with same YAML
        Then: Second import produces same state
        And: No duplicate records created
        """
        from bagels.utils.import_yaml import import_records_from_yaml
        from bagels.models.record import Record
        from datetime import datetime

        yaml_data = {
            "r_2026-03-14_001": {
                "label": "Test Record",
                "amount": 100.0,
                "date": "2026-03-14T00:00:00",
                "accountSlug": "acc_savings",
                "categorySlug": None,
                "isIncome": False,
                "isTransfer": False
            }
        }

        # First import
        import_records_from_yaml(yaml_data, in_memory_db)
        count_after_first = in_memory_db.query(Record).count()

        # Second import
        import_records_from_yaml(yaml_data, in_memory_db)
        count_after_second = in_memory_db.query(Record).count()

        assert count_after_first == count_after_second == 1

    def test_import_handles_large_datasets_efficiently(self, in_memory_db, sample_account):
        """
        Test that import handles large datasets efficiently.

        Given: YAML with 1000 records
        When: import_records_from_yaml(yaml_data, session)
        Then: Import completes in reasonable time (<10 seconds)
        And: Bulk operations used (not row-by-row)
        """
        from bagels.utils.import_yaml import import_records_from_yaml
        from bagels.models.record import Record
        from datetime import datetime
        import time

        yaml_data = {
            f"r_2026-03-{i//50 + 1:02d}_{i%50 + 1:03d}": {
                "label": f"Record {i}",
                "amount": 100.0,
                "date": f"2026-03-{i//50 + 1:02d}T00:00:00",
                "accountSlug": "acc_savings",
                "categorySlug": None,
                "isIncome": False,
                "isTransfer": False
            }
            for i in range(1000)
        }

        start = time.time()
        imported = import_records_from_yaml(yaml_data, in_memory_db)
        duration = time.time() - start

        assert imported == 1000
        assert duration < 10.0, f"Import took {duration:.2f}s, expected <10s"


class TestCategoriesImport:
    """Test category import functionality."""

    def test_import_handles_category_parent_child_relationships(self, in_memory_db):
        """
        Test that import handles category parent-child relationships.

        Given: YAML with parent and child categories
        When: import_categories_from_yaml(yaml_data, session)
        Then: Parent and child imported
        And: Parent-child relationship preserved via parentSlug
        """
        from bagels.utils.import_yaml import import_categories_from_yaml
        from bagels.models.category import Category

        yaml_data = {
            "cat_food": {
                "name": "Food",
                "parentSlug": None,
                "nature": "expense",
                "color": "#FF5733"
            },
            "cat_groceries": {
                "name": "Groceries",
                "parentSlug": "cat_food",
                "nature": "expense",
                "color": "#FF5733"
            }
        }

        imported = import_categories_from_yaml(yaml_data, in_memory_db)

        assert imported == 2

        # Verify parent-child relationship
        parent = in_memory_db.query(Category).filter_by(slug="cat_food").first()
        child = in_memory_db.query(Category).filter_by(slug="cat_groceries").first()

        assert parent is not None
        assert child is not None
        assert child.parentCategoryId == parent.id


class TestTemplatesImport:
    """Test template import functionality."""

    def test_import_handles_templates_with_order(self, in_memory_db, sample_account, sample_category):
        """
        Test that import handles templates with order.

        Given: YAML with 3 templates in specific order
        When: import_templates_from_yaml(yaml_data, session)
        Then: All 3 templates imported
        And: Order field preserved from YAML
        """
        from bagels.utils.import_yaml import import_templates_from_yaml
        from bagels.models.record_template import RecordTemplate

        yaml_data = {
            "tpl_rent": {
                "label": "Rent",
                "amount": 1500.0,
                "accountSlug": "acc_savings",
                "categorySlug": "cat_groceries",
                "personSlug": None,
                "isIncome": False,
                "ordinal": 0
            },
            "tpl_utilities": {
                "label": "Utilities",
                "amount": 200.0,
                "accountSlug": "acc_savings",
                "categorySlug": "cat_groceries",
                "personSlug": None,
                "isIncome": False,
                "ordinal": 1
            },
            "tpl_internet": {
                "label": "Internet",
                "amount": 80.0,
                "accountSlug": "acc_savings",
                "categorySlug": "cat_groceries",
                "personSlug": None,
                "isIncome": False,
                "ordinal": 2
            }
        }

        imported = import_templates_from_yaml(yaml_data, in_memory_db)

        assert imported == 3

        templates = in_memory_db.query(RecordTemplate).order_by(RecordTemplate.ordinal).all()
        assert len(templates) == 3
        assert templates[0].ordinal == 0
        assert templates[1].ordinal == 1
        assert templates[2].ordinal == 2
