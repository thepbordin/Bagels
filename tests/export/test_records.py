"""
Tests for record export with monthly grouping.

Tests verify that records can be exported to YAML files organized by month
(YYYY-MM.yaml) with slug-based IDs for mergeability.
"""

import pytest
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session


class TestRecordExportSingleMonth:
    """Test exporting records for a single month."""

    def test_export_five_records_from_march_2026(
        self, in_memory_db: Session, temp_directory: Path, sample_records
    ):
        """
        Given: 5 records all in March 2026
        When: export_records_by_month(session, temp_dir)
        Then: File created at temp_dir/records/2026-03.yaml
        And: YAML contains all 5 records
        And: Records keyed by slug (r_2026-03-14_001 format)
        """
        # Arrange - All records should be in March 2026
        # sample_records fixture creates records from March 1-5, 2026

        # Act - Export records (function doesn't exist yet - TDD RED phase)
        from bagels.export.records import export_records_by_month

        export_records_by_month(in_memory_db, temp_directory)

        # Assert - Verify file exists
        records_dir = temp_directory / "records"
        yaml_file = records_dir / "2026-03.yaml"
        assert yaml_file.exists(), "YAML file should be created for March 2026"

        # Assert - Verify YAML content
        import yaml

        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f)

        assert "records" in data, "YAML should contain records key"
        assert len(data["records"]) == 5, "All 5 records should be exported"

        # Assert - Verify slug-based IDs
        for slug in data["records"].keys():
            assert slug.startswith("r_2026-03-"), (
                f"Slug {slug} should use r_YYYY-MM-DD_### format"
            )
            assert "_" in slug, "Slug should have underscore separators"


class TestRecordExportMultipleMonths:
    """Test exporting records across multiple months."""

    def test_export_ten_records_across_jan_feb_mar_2026(
        self, in_memory_db: Session, temp_directory: Path
    ):
        """
        Given: 10 records across Jan, Feb, Mar 2026
        When: export_records_by_month(session, temp_dir)
        Then: 3 files created: 2026-01.yaml, 2026-02.yaml, 2026-03.yaml
        And: Each file contains only records for that month
        And: No records in wrong month file
        """
        from bagels.models.account import Account
        from bagels.models.category import Category
        from bagels.models.record import Record

        # Arrange - Create test data
        account = Account(name="Test Account", beginningBalance=1000.0)
        in_memory_db.add(account)
        category = Category(name="Test Category", nature="expense")
        in_memory_db.add(category)
        in_memory_db.commit()

        # Create records across 3 months
        dates = [
            datetime(2026, 1, 5),  # January
            datetime(2026, 1, 15),
            datetime(2026, 1, 25),
            datetime(2026, 2, 5),  # February
            datetime(2026, 2, 15),
            datetime(2026, 2, 25),
            datetime(2026, 3, 5),  # March
            datetime(2026, 3, 15),
            datetime(2026, 3, 25),
            datetime(2026, 3, 30),
        ]

        for i, date in enumerate(dates):
            record = Record(
                label=f"Record {i + 1}",
                amount=100.0 * (i + 1),
                date=date,
                accountId=account.id,
                categoryId=category.id,
                isIncome=False,
                isTransfer=False,
            )
            in_memory_db.add(record)

        in_memory_db.commit()

        # Act - Export records
        from bagels.export.records import export_records_by_month

        export_records_by_month(in_memory_db, temp_directory)

        # Assert - Verify 3 files created
        records_dir = temp_directory / "records"
        assert (records_dir / "2026-01.yaml").exists(), "January file should exist"
        assert (records_dir / "2026-02.yaml").exists(), "February file should exist"
        assert (records_dir / "2026-03.yaml").exists(), "March file should exist"

        # Assert - Verify each file has correct count
        import yaml

        with open(records_dir / "2026-01.yaml", "r") as f:
            jan_data = yaml.safe_load(f)
        with open(records_dir / "2026-02.yaml", "r") as f:
            feb_data = yaml.safe_load(f)
        with open(records_dir / "2026-03.yaml", "r") as f:
            mar_data = yaml.safe_load(f)

        assert len(jan_data["records"]) == 3, "January should have 3 records"
        assert len(feb_data["records"]) == 3, "February should have 3 records"
        assert len(mar_data["records"]) == 4, "March should have 4 records"

        # Assert - Verify no cross-contamination
        jan_dates = [r["date"][:7] for r in jan_data["records"].values()]
        feb_dates = [r["date"][:7] for r in feb_data["records"].values()]
        mar_dates = [r["date"][:7] for r in mar_data["records"].values()]

        assert all(d == "2026-01" for d in jan_dates), (
            "All January records should be in January file"
        )
        assert all(d == "2026-02" for d in feb_dates), (
            "All February records should be in February file"
        )
        assert all(d == "2026-03" for d in mar_dates), (
            "All March records should be in March file"
        )


class TestRecordSlugGeneration:
    """Test slug-based ID generation for records."""

    def test_slug_sequence_increments_for_same_date(
        self, in_memory_db: Session, temp_directory: Path
    ):
        """
        Given: 3 records on same date (2026-03-14)
        When: Exported to YAML
        Then: Slugs are r_2026-03-14_001, r_2026-03-14_002, r_2026-03-14_003
        And: Sequence numbers increment correctly
        """
        from bagels.models.account import Account
        from bagels.models.category import Category
        from bagels.models.record import Record

        # Arrange - Create 3 records on same date
        account = Account(name="Test Account", beginningBalance=1000.0)
        in_memory_db.add(account)
        category = Category(name="Test Category", nature="expense")
        in_memory_db.add(category)
        in_memory_db.commit()

        test_date = datetime(2026, 3, 14)
        for i in range(3):
            record = Record(
                label=f"Record {i + 1}",
                amount=100.0 * (i + 1),
                date=test_date,
                accountId=account.id,
                categoryId=category.id,
                isIncome=False,
                isTransfer=False,
            )
            in_memory_db.add(record)

        in_memory_db.commit()

        # Act - Export records
        from bagels.export.records import export_records_by_month

        export_records_by_month(in_memory_db, temp_directory)

        # Assert - Verify slug generation
        import yaml

        yaml_file = temp_directory / "records" / "2026-03.yaml"
        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f)

        slugs = list(data["records"].keys())
        assert "r_2026-03-14_001" in slugs, "First slug should be r_2026-03-14_001"
        assert "r_2026-03-14_002" in slugs, "Second slug should be r_2026-03-14_002"
        assert "r_2026-03-14_003" in slugs, "Third slug should be r_2026-03-14_003"


class TestRecordExportFields:
    """Test that all record fields are exported correctly."""

    def test_export_includes_all_record_fields(
        self, in_memory_db: Session, temp_directory: Path
    ):
        """
        Given: Record with label, amount, date, accountId, categoryId, personId, isIncome, isTransfer
        When: Exported to YAML
        Then: All fields present
        And: Foreign keys use slug references
        And: Timestamps in ISO format
        And: Amount is float with proper precision (2 decimals)
        """
        from bagels.models.account import Account
        from bagels.models.category import Category
        from bagels.models.person import Person
        from bagels.models.record import Record

        # Arrange - Create record with all fields
        account = Account(name="Test Account", beginningBalance=1000.0)
        in_memory_db.add(account)
        category = Category(name="Test Category", nature="expense")
        in_memory_db.add(category)
        person = Person(name="John Doe")
        in_memory_db.add(person)
        in_memory_db.commit()

        record = Record(
            label="Test Record",
            amount=123.456,  # Should round to 2 decimals
            date=datetime(2026, 3, 14, 10, 30, 0),
            accountId=account.id,
            categoryId=category.id,
            personId=person.id,
            isIncome=False,
            isTransfer=False,
        )
        in_memory_db.add(record)
        in_memory_db.commit()

        # Act - Export records
        from bagels.export.records import export_records_by_month

        export_records_by_month(in_memory_db, temp_directory)

        # Assert - Verify all fields present
        import yaml

        yaml_file = temp_directory / "records" / "2026-03.yaml"
        with open(yaml_file, "r") as f:
            data = yaml.safe_load(f)

        # Get the first (and only) record
        record_data = list(data["records"].values())[0]

        # Check all required fields
        assert "label" in record_data, "Record should have label"
        assert "amount" in record_data, "Record should have amount"
        assert "date" in record_data, "Record should have date"
        assert "accountSlug" in record_data, "Record should reference account by slug"
        assert "categorySlug" in record_data, "Record should reference category by slug"
        assert "personSlug" in record_data, "Record should reference person by slug"
        assert "isIncome" in record_data, "Record should have isIncome"
        assert "isTransfer" in record_data, "Record should have isTransfer"
        assert "createdAt" in record_data, "Record should have createdAt timestamp"
        assert "updatedAt" in record_data, "Record should have updatedAt timestamp"

        # Verify field values
        assert record_data["label"] == "Test Record"
        assert record_data["amount"] == 123.46  # Rounded to 2 decimals
        assert "2026-03-14" in record_data["date"]
        assert record_data["isIncome"] is False
        assert record_data["isTransfer"] is False

        # Verify ISO timestamp format
        assert "T" in record_data["createdAt"], "Timestamp should be ISO format"
        assert "T" in record_data["updatedAt"], "Timestamp should be ISO format"


class TestRecordExportEmpty:
    """Test exporting when no records exist."""

    def test_export_handles_empty_months(
        self, in_memory_db: Session, temp_directory: Path
    ):
        """
        Given: No records in database
        When: export_records_by_month(session, temp_dir)
        Then: No files created (or empty directory)
        And: No errors thrown
        """
        # Arrange - No records in database (in_memory_db is empty)

        # Act - Export records (should not error)
        from bagels.export.records import export_records_by_month

        export_records_by_month(in_memory_db, temp_directory)

        # Assert - No files created
        records_dir = temp_directory / "records"
        if records_dir.exists():
            yaml_files = list(records_dir.glob("*.yaml"))
            assert len(yaml_files) == 0, (
                "No YAML files should be created when no records exist"
            )


# ---------------------------------------------------------------------------
# Tests for export_records_for_month (targeted single-month export)
# ---------------------------------------------------------------------------


class TestExportRecordsForMonth:
    """Test the targeted single-month export helper."""

    def _make_records(self, session, dates: list[datetime]) -> None:
        """Helper: create minimal records on the given dates."""
        from bagels.models.account import Account
        from bagels.models.category import Category
        from bagels.models.record import Record

        account = Account(name="Test Account", beginningBalance=0.0)
        session.add(account)
        session.flush()
        from bagels.models.category import Nature

        category = Category(name="Test Category", nature=Nature.NEED, color="#AABBCC")
        session.add(category)
        session.flush()

        for i, date in enumerate(dates):
            record = Record(
                label=f"Record {i + 1}",
                amount=float(10 * (i + 1)),
                date=date,
                accountId=account.id,
                categoryId=category.id,
                isIncome=False,
                isTransfer=False,
            )
            session.add(record)

        session.commit()

    def test_export_for_month_with_records_writes_yaml(
        self, in_memory_db: Session, temp_directory: Path
    ):
        """
        Test 1: export_records_for_month with records in that month writes records/YYYY-MM.yaml.
        """
        self._make_records(
            in_memory_db,
            [datetime(2026, 3, 1), datetime(2026, 3, 15), datetime(2026, 3, 31)],
        )

        from bagels.export.exporter import export_records_for_month

        filepath = export_records_for_month(in_memory_db, temp_directory, 2026, 3)

        assert filepath.exists(), "YAML file should be written"
        assert filepath == temp_directory / "records" / "2026-03.yaml"

        import yaml

        with open(filepath) as f:
            data = yaml.safe_load(f)

        assert "records" in data
        assert len(data["records"]) == 3

    def test_export_for_month_with_no_records_writes_empty_file(
        self, in_memory_db: Session, temp_directory: Path
    ):
        """
        Test 2: export_records_for_month with NO records writes records/YYYY-MM.yaml
        with empty records dict (not skipping the file).
        """
        from bagels.export.exporter import export_records_for_month

        filepath = export_records_for_month(in_memory_db, temp_directory, 2026, 4)

        assert filepath.exists(), "File must be written even for an empty month"

        import yaml

        with open(filepath) as f:
            data = yaml.safe_load(f)

        assert "records" in data
        assert data["records"] == {} or data["records"] is None

    def test_export_for_month_excludes_adjacent_months(
        self, in_memory_db: Session, temp_directory: Path
    ):
        """
        Test 3: export_records_for_month only includes records from the specified month.
        """
        self._make_records(
            in_memory_db,
            [
                datetime(2026, 2, 28),  # February — must NOT appear
                datetime(2026, 3, 1),  # March
                datetime(2026, 3, 15),  # March
                datetime(2026, 4, 1),  # April — must NOT appear
            ],
        )

        from bagels.export.exporter import export_records_for_month

        filepath = export_records_for_month(in_memory_db, temp_directory, 2026, 3)

        import yaml

        with open(filepath) as f:
            data = yaml.safe_load(f)

        assert len(data["records"]) == 2, "Only March records should be included"
        for record_data in data["records"].values():
            assert record_data["date"].startswith("2026-03"), (
                "All records should be from March 2026"
            )
