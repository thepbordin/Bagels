"""
Tests for slug-based ID generation logic.

Tests verify that record slugs are generated correctly with date-based
prefixes and sequential numbering, enabling merge-by-ID workflows.
"""

import pytest
from datetime import date
from sqlalchemy.orm import Session


class TestSlugGenerationFirstOfDay:
    """Test generating the first slug for a given date."""

    def test_generate_first_slug_of_day(self, in_memory_db: Session):
        """
        Given: No existing records for date 2026-03-14
        When: generate_record_slug(date(2026, 3, 14), session)
        Then: Returns "r_2026-03-14_001"
        """
        from bagels.export.slug_generator import generate_record_slug

        test_date = date(2026, 3, 14)
        slug = generate_record_slug(test_date, in_memory_db)

        assert slug == "r_2026-03-14_001", f"First slug should be r_2026-03-14_001, got {slug}"


class TestSlugGenerationSequential:
    """Test generating sequential slugs for the same date."""

    def test_generate_sequential_slugs_for_same_day(self, in_memory_db: Session):
        """
        Given: 2 existing records with slugs r_2026-03-14_001, r_2026-03-14_002
        When: generate_record_slug(date(2026, 3, 14), session)
        Then: Returns "r_2026-03-14_003"
        """
        from bagels.models.record import Record
        from bagels.models.account import Account
        from bagels.models.category import Category
        from bagels.models.category import Nature

        # Create account and category
        account = Account(name="Test Account", beginningBalance=1000.0)
        in_memory_db.add(account)
        category = Category(name="Test Category", nature=Nature.NEED, color="#FF0000")
        in_memory_db.add(category)
        in_memory_db.commit()

        # Create 2 existing records with known slugs
        test_date = date(2026, 3, 14)

        record1 = Record(
            label="Record 1",
            amount=100.0,
            date=test_date,
            accountId=account.id,
            categoryId=category.id,
            isIncome=False,
            isTransfer=False
        )
        in_memory_db.add(record1)
        in_memory_db.flush()

        # Manually set slug (simulating previous exports)
        record1.slug = "r_2026-03-14_001"

        record2 = Record(
            label="Record 2",
            amount=200.0,
            date=test_date,
            accountId=account.id,
            categoryId=category.id,
            isIncome=False,
            isTransfer=False
        )
        in_memory_db.add(record2)
        in_memory_db.flush()

        # Manually set slug
        record2.slug = "r_2026-03-14_002"

        in_memory_db.commit()

        # Generate next slug
        from bagels.export.slug_generator import generate_record_slug

        slug = generate_record_slug(test_date, in_memory_db)

        assert slug == "r_2026-03-14_003", f"Third slug should be r_2026-03-14_003, got {slug}"


class TestSlugGenerationDifferentDay:
    """Test that sequence resets for different dates."""

    def test_generate_slug_for_different_day(self, in_memory_db: Session):
        """
        Given: Records exist for 2026-03-14
        When: generate_record_slug(date(2026, 3, 15), session)
        Then: Returns "r_2026-03-15_001" (resets sequence)
        """
        from bagels.models.record import Record
        from bagels.models.account import Account
        from bagels.models.category import Category
        from bagels.models.category import Nature

        # Create account and category
        account = Account(name="Test Account", beginningBalance=1000.0)
        in_memory_db.add(account)
        category = Category(name="Test Category", nature=Nature.NEED, color="#FF0000")
        in_memory_db.add(category)
        in_memory_db.commit()

        # Create record on 2026-03-14
        test_date_1 = date(2026, 3, 14)
        record1 = Record(
            label="Record 1",
            amount=100.0,
            date=test_date_1,
            accountId=account.id,
            categoryId=category.id,
            isIncome=False,
            isTransfer=False
        )
        in_memory_db.add(record1)
        in_memory_db.flush()
        record1.slug = "r_2026-03-14_001"
        in_memory_db.commit()

        # Generate slug for different day
        from bagels.export.slug_generator import generate_record_slug

        test_date_2 = date(2026, 3, 15)
        slug = generate_record_slug(test_date_2, in_memory_db)

        assert slug == "r_2026-03-15_001", f"New day should reset to 001, got {slug}"


class TestSlugGenerationGaps:
    """Test handling gaps in sequence numbers."""

    def test_handle_gaps_in_sequence(self, in_memory_db: Session):
        """
        Given: Only r_2026-03-14_001 and r_2026-03-14_005 exist
        When: generate_record_slug(date(2026, 3, 14), session)
        Then: Returns "r_2026-03-14_006" (fills next, not gap)
        """
        from bagels.models.record import Record
        from bagels.models.account import Account
        from bagels.models.category import Category
        from bagels.models.category import Nature

        # Create account and category
        account = Account(name="Test Account", beginningBalance=1000.0)
        in_memory_db.add(account)
        category = Category(name="Test Category", nature=Nature.NEED, color="#FF0000")
        in_memory_db.add(category)
        in_memory_db.commit()

        # Create records with gap (001 and 005, missing 002-004)
        test_date = date(2026, 3, 14)

        record1 = Record(
            label="Record 1",
            amount=100.0,
            date=test_date,
            accountId=account.id,
            categoryId=category.id,
            isIncome=False,
            isTransfer=False
        )
        in_memory_db.add(record1)
        in_memory_db.flush()
        record1.slug = "r_2026-03-14_001"

        record5 = Record(
            label="Record 5",
            amount=500.0,
            date=test_date,
            accountId=account.id,
            categoryId=category.id,
            isIncome=False,
            isTransfer=False
        )
        in_memory_db.add(record5)
        in_memory_db.flush()
        record5.slug = "r_2026-03-14_005"

        in_memory_db.commit()

        # Generate next slug
        from bagels.export.slug_generator import generate_record_slug

        slug = generate_record_slug(test_date, in_memory_db)

        assert slug == "r_2026-03-14_006", f"Should fill next available (006), not gap, got {slug}"


class TestSlugGenerationMissingSlugs:
    """Test handling records without slug field."""

    def test_handle_records_without_slugs(self, in_memory_db: Session):
        """
        Given: Old records with no slug field
        When: generate_record_slug(date, session)
        Then: Ignores records without slugs
        And: Returns correct next sequence
        """
        from bagels.models.record import Record
        from bagels.models.account import Account
        from bagels.models.category import Category
        from bagels.models.category import Nature

        # Create account and category
        account = Account(name="Test Account", beginningBalance=1000.0)
        in_memory_db.add(account)
        category = Category(name="Test Category", nature=Nature.NEED, color="#FF0000")
        in_memory_db.add(category)
        in_memory_db.commit()

        # Create records without slugs (old records)
        test_date = date(2026, 3, 14)

        for i in range(3):
            record = Record(
                label=f"Record {i+1}",
                amount=100.0 * (i + 1),
                date=test_date,
                accountId=account.id,
                categoryId=category.id,
                isIncome=False,
                isTransfer=False
            )
            # Intentionally NOT setting slug (old records)
            in_memory_db.add(record)

        in_memory_db.commit()

        # Generate slug
        from bagels.export.slug_generator import generate_record_slug

        slug = generate_record_slug(test_date, in_memory_db)

        # Should return 001 since no records have slugs
        assert slug == "r_2026-03-14_001", f"Should ignore records without slugs and return 001, got {slug}"


class TestSlugFormatValidation:
    """Test slug format validation."""

    def test_validate_slug_format(self, in_memory_db: Session):
        """
        Given: Generated slug
        When: Checked with regex
        Then: Matches pattern r_YYYY-MM-DD_###
        """
        import re

        from bagels.export.slug_generator import generate_record_slug

        test_date = date(2026, 3, 14)
        slug = generate_record_slug(test_date, in_memory_db)

        # Regex pattern: r_YYYY-MM-DD_###
        pattern = r"^r_\d{4}-\d{2}-\d{2}_\d{3}$"

        assert re.match(pattern, slug), f"Slug {slug} doesn't match pattern r_YYYY-MM-DD_###"

        # Also verify the date part is correct
        assert "2026-03-14" in slug, f"Slug should contain date 2026-03-14, got {slug}"
        assert slug.endswith("_001"), f"First slug should end with _001, got {slug}"
