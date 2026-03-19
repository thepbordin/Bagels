"""
Integration tests for bidirectional SQLite<->YAML sync.

Validates the core system guarantee: data written to SQLite can be exported
to YAML and re-imported without loss or drift across repeated cycles.

Tests:
- 3 full round-trip cycles for accounts and records
- Slug preservation across all 3 cycles
- Backup file creation on import
- Corrupt YAML causes safe failure without silent DB corruption
"""

import re
import yaml
import pytest
from datetime import datetime

from bagels.export.exporter import (
    export_accounts,
    export_records_for_month,
)
from bagels.importer.importer import (
    import_accounts_from_yaml,
    import_records_from_yaml,
)
from bagels.models.account import Account
from bagels.models.record import Record


class TestRoundTripSync:
    """3-cycle round-trip sync tests for accounts and records."""

    def test_accounts_3_cycle_round_trip(self, in_memory_db, temp_directory):
        """3 full export->import cycles preserve all account field values."""
        # Create a test account
        account = Account(
            name="Cycle Test",
            slug="cycle-test",
            beginningBalance=500.0,
            hidden=False,
        )
        in_memory_db.add(account)
        in_memory_db.commit()

        # Capture original field values
        original_name = account.name
        original_balance = account.beginningBalance
        original_hidden = account.hidden
        original_slug = account.slug

        for cycle in range(3):
            # Export to YAML
            yaml_path = export_accounts(in_memory_db, temp_directory)
            assert yaml_path.exists(), f"accounts.yaml not found after cycle {cycle}"

            # Read YAML
            with open(yaml_path) as f:
                yaml_data = yaml.safe_load(f)

            # Re-import into same session
            import_accounts_from_yaml(yaml_data, in_memory_db)

            # Re-query by slug
            reimported = (
                in_memory_db.query(Account).filter(Account.slug == "cycle-test").first()
            )
            assert reimported is not None, f"Account not found after cycle {cycle}"

            # Assert field fidelity
            assert reimported.name == original_name, (
                f"Cycle {cycle}: name mismatch: {reimported.name!r} != {original_name!r}"
            )
            assert reimported.beginningBalance == original_balance, (
                f"Cycle {cycle}: beginningBalance mismatch: "
                f"{reimported.beginningBalance} != {original_balance}"
            )
            assert reimported.hidden == original_hidden, (
                f"Cycle {cycle}: hidden mismatch: {reimported.hidden} != {original_hidden}"
            )
            assert reimported.slug == original_slug, (
                f"Cycle {cycle}: slug changed from {original_slug!r} to {reimported.slug!r}"
            )

        # Final check: YAML file exists after all cycles
        assert (temp_directory / "accounts.yaml").exists()

    def test_records_3_cycle_round_trip(
        self, in_memory_db, temp_directory, sample_account, sample_category
    ):
        """3 full export->import cycles preserve all record field values including slug."""
        # Give sample_account and sample_category real slugs so the validator
        # can find them by slug during import.
        sample_account.slug = "acc-cycle-test"
        sample_category.slug = "cat-cycle-test"
        in_memory_db.commit()

        # Create a test record
        record = Record(
            label="Cycle Coffee",
            amount=4.50,
            date=datetime(2026, 3, 14),
            accountId=sample_account.id,
            categoryId=sample_category.id,
            isIncome=False,
            isTransfer=False,
        )
        in_memory_db.add(record)
        in_memory_db.flush()

        # Export first to trigger slug assignment
        export_records_for_month(in_memory_db, temp_directory, 2026, 3)
        in_memory_db.commit()

        # Re-query to get the slug assigned by exporter
        in_memory_db.refresh(record)
        captured_slug = record.slug
        assert captured_slug is not None, "Slug was not assigned after first export"
        assert re.match(r"r_2026-03-14_\d{3}", captured_slug), (
            f"Slug format invalid: {captured_slug!r}"
        )

        # Capture original field values
        original_label = record.label
        original_amount = record.amount
        original_is_income = record.isIncome
        original_is_transfer = record.isTransfer

        for cycle in range(3):
            # Export
            yaml_path = export_records_for_month(in_memory_db, temp_directory, 2026, 3)

            # Read YAML
            with open(yaml_path) as f:
                yaml_data = yaml.safe_load(f)

            # Re-import
            import_records_from_yaml(yaml_data, in_memory_db)

            # Re-query by slug
            reimported = (
                in_memory_db.query(Record).filter(Record.slug == captured_slug).first()
            )
            assert reimported is not None, (
                f"Record with slug {captured_slug!r} not found after cycle {cycle}"
            )

            # Assert field fidelity
            assert reimported.label == original_label, (
                f"Cycle {cycle}: label mismatch: {reimported.label!r} != {original_label!r}"
            )
            assert reimported.amount == original_amount, (
                f"Cycle {cycle}: amount mismatch: {reimported.amount} != {original_amount}"
            )
            assert reimported.isIncome == original_is_income, (
                f"Cycle {cycle}: isIncome mismatch"
            )
            assert reimported.isTransfer == original_is_transfer, (
                f"Cycle {cycle}: isTransfer mismatch"
            )
            assert reimported.slug == captured_slug, (
                f"Cycle {cycle}: slug changed from {captured_slug!r} to {reimported.slug!r}"
            )

        # Final check: records YAML file exists
        assert (temp_directory / "records" / "2026-03.yaml").exists()

    def test_slug_preservation_across_cycles(
        self, in_memory_db, temp_directory, sample_account, sample_category
    ):
        """Slugs for 3 records on the same date are stable across 3 round-trip cycles."""
        # Give sample_account and sample_category real slugs so the validator
        # can find them by slug during import.
        sample_account.slug = "acc-slug-test"
        sample_category.slug = "cat-slug-test"
        in_memory_db.commit()

        # Create 3 records on the same date
        records_data = [
            ("Slug Test A", 10.0),
            ("Slug Test B", 20.0),
            ("Slug Test C", 30.0),
        ]
        created_records = []
        for label, amount in records_data:
            rec = Record(
                label=label,
                amount=amount,
                date=datetime(2026, 3, 15),
                accountId=sample_account.id,
                categoryId=sample_category.id,
                isIncome=False,
                isTransfer=False,
            )
            in_memory_db.add(rec)
            created_records.append(rec)

        in_memory_db.flush()

        # Export once to trigger slug assignment
        export_records_for_month(in_memory_db, temp_directory, 2026, 3)
        in_memory_db.commit()

        # Capture all 3 slugs
        slugs = {}
        for rec in created_records:
            in_memory_db.refresh(rec)
            assert rec.slug is not None, f"Slug not assigned for record {rec.label!r}"
            slugs[rec.slug] = rec.label

        assert len(slugs) == 3, f"Expected 3 unique slugs, got {len(slugs)}: {slugs}"

        # Run 3 round-trip cycles
        for cycle in range(3):
            yaml_path = export_records_for_month(in_memory_db, temp_directory, 2026, 3)
            with open(yaml_path) as f:
                yaml_data = yaml.safe_load(f)
            import_records_from_yaml(yaml_data, in_memory_db)

            # After each cycle: all 3 slugs must still exist mapping to correct labels
            for slug, expected_label in slugs.items():
                reimported = (
                    in_memory_db.query(Record).filter(Record.slug == slug).first()
                )
                assert reimported is not None, (
                    f"Cycle {cycle}: record with slug {slug!r} missing"
                )
                assert reimported.label == expected_label, (
                    f"Cycle {cycle}: slug {slug!r} now maps to {reimported.label!r}, "
                    f"expected {expected_label!r}"
                )


class TestBackupCreation:
    """Tests that import operations create database backups."""

    def test_backup_created_after_import(
        self, in_memory_db, temp_directory, sample_account, tmp_path
    ):
        """A backup file is created in the backups directory after import_accounts_from_yaml."""
        from bagels.locations import set_custom_root

        # Redirect all app paths to use tmp_path as the root
        set_custom_root(tmp_path)
        try:
            # create_backup() copies database_file() if it exists.
            # With an in-memory DB there is no file at database_file(), so we need
            # to seed a dummy db file at the expected path to exercise the copy path.
            from bagels.locations import database_file

            db_path = database_file()
            db_path.write_bytes(b"SQLite format 3\x00")  # minimal SQLite header stub

            # Export accounts
            yaml_path = export_accounts(in_memory_db, temp_directory)
            with open(yaml_path) as f:
                yaml_data = yaml.safe_load(f)

            # Import (triggers backup creation)
            import_accounts_from_yaml(yaml_data, in_memory_db)

            # Verify backup was created
            backups_dir = tmp_path / "backups"
            backup_files = list(backups_dir.glob("backup_*.db"))
            assert len(backup_files) >= 1, (
                f"Expected at least one backup_*.db in {backups_dir}, found none. "
                f"Contents: {list(backups_dir.iterdir()) if backups_dir.exists() else 'directory missing'}"
            )
        finally:
            set_custom_root(None)


class TestCorruptYaml:
    """Tests that corrupt YAML fails gracefully without silent DB corruption."""

    def test_corrupt_yaml_fails_gracefully(
        self, in_memory_db, temp_directory, sample_account
    ):
        """Corrupt YAML (git conflict markers) causes an exception; DB is not silently corrupted."""
        original_slug = sample_account.slug or f"acc_{sample_account.id}"

        # Export clean accounts.yaml
        yaml_path = export_accounts(in_memory_db, temp_directory)
        with open(yaml_path) as f:
            clean_content = f.read()

        # Prepend git conflict markers
        conflict_prefix = "<<<<<<< HEAD\nconflict content\n=======\n"
        corrupted_content = conflict_prefix + clean_content
        with open(yaml_path, "w") as f:
            f.write(corrupted_content)

        # Attempt to load corrupted YAML
        exception_raised = False
        try:
            with open(yaml_path) as f:
                garbage_data = yaml.safe_load(f)

            # If yaml.safe_load returns without error, call the importer
            # The importer or validator should raise an exception
            if garbage_data is not None:
                import_accounts_from_yaml(garbage_data, in_memory_db)
        except (yaml.YAMLError, Exception):
            exception_raised = True

        # An exception MUST have been raised — no silent corruption allowed
        assert exception_raised, (
            "Expected an exception when processing corrupt YAML, but none was raised. "
            "Silent data corruption may have occurred."
        )

        # DB integrity: original account must still be present
        # Query by name since slug might be acc_N when no slug field set
        from_db = (
            in_memory_db.query(Account)
            .filter(Account.name == sample_account.name)
            .first()
        )
        assert from_db is not None, (
            f"Original account {sample_account.name!r} missing after corrupt import attempt"
        )
