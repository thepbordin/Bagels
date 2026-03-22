"""
Integration tests for records query commands.

Tests the bagels records list and show commands with various filters
and output formats.
"""

import json
from unittest.mock import patch
from click.testing import CliRunner
from bagels.models.record import Record
from bagels.models.category import Category
from bagels.models.account import Account
from bagels.cli.records import records


def test_records_list_default(sample_db_with_records, cli_runner):
    """Test listing records without filters (table format)."""
    # Mock Session to return test database
    with patch("bagels.cli.records.Session", return_value=sample_db_with_records):
        result = cli_runner.invoke(records, ["list"])

    assert result.exit_code == 0
    assert "Records" in result.output
    # Check for table headers (may be truncated)
    assert "ID" in result.output
    assert "Date" in result.output
    assert "Label" in result.output
    assert "Amo" in result.output  # May be truncated to "Amo..."
    assert "Category" in result.output
    assert "Account" in result.output


def test_records_list_month(sample_db_with_records, cli_runner):
    """Test filtering records by month."""
    from datetime import datetime

    # Get current month
    current_month = datetime.now().strftime("%Y-%m")

    result = cli_runner.invoke(records, ["list", "--month", current_month])

    assert result.exit_code == 0
    assert "Records" in result.output


def test_records_list_date_range(sample_db_with_records, cli_runner):
    """Test filtering records by date range."""
    result = cli_runner.invoke(
        records, ["list", "--date-from", "2026-01-01", "--date-to", "2026-12-31"]
    )

    assert result.exit_code == 0
    assert "Records" in result.output


def test_records_filter_category(sample_db_with_records, cli_runner):
    """Test filtering records by category name."""
    # Get first category name
    session = sample_db_with_records
    category = session.query(Category).first()

    result = cli_runner.invoke(records, ["list", "--category", category.name])

    assert result.exit_code == 0
    assert "Records" in result.output


def test_records_filter_amount(sample_db_with_records, cli_runner):
    """Test filtering records by amount range."""
    result = cli_runner.invoke(records, ["list", "--amount", "30..60"])

    assert result.exit_code == 0
    assert "Records" in result.output


def test_records_filter_account(sample_db_with_records, cli_runner):
    """Test filtering records by account name."""
    # Get first account name
    session = sample_db_with_records
    account = session.query(Account).first()

    result = cli_runner.invoke(records, ["list", "--account", account.name])

    assert result.exit_code == 0
    assert "Records" in result.output


def test_records_format_json(sample_db_with_records, cli_runner):
    """Test JSON output format."""
    result = cli_runner.invoke(records, ["list", "--format", "json"])

    assert result.exit_code == 0
    # Check for valid JSON
    try:
        data = json.loads(result.output)
        assert isinstance(data, list)
    except json.JSONDecodeError:
        assert False, "Output is not valid JSON"


def test_records_format_yaml(sample_db_with_records, cli_runner):
    """Test YAML output format."""
    result = cli_runner.invoke(records, ["list", "--format", "yaml"])

    assert result.exit_code == 0
    # Check for YAML-like structure
    assert "- id:" in result.output or "id:" in result.output


def test_records_limit_default(sample_db_with_records, cli_runner):
    """Test default limit of 50 records."""
    result = cli_runner.invoke(records, ["list"])

    assert result.exit_code == 0
    # Should show warning if we have more than 50 records
    # (our fixture creates ~27 records per month * 3 months = ~81 records)
    if "Showing 50 most recent records" in result.output:
        assert "Use --all to see all records" in result.output


def test_records_limit_all(sample_db_with_records, cli_runner):
    """Test --all flag removes limit."""
    result = cli_runner.invoke(records, ["list", "--all"])

    assert result.exit_code == 0
    # Should NOT show limit warning
    assert "Showing 50 most recent records" not in result.output
    assert "Use --all to see all records" not in result.output


def test_records_show_valid(sample_db_with_records, cli_runner):
    """Test showing a single record by ID."""
    # Get first record
    session = sample_db_with_records
    record = session.query(Record).first()

    result = cli_runner.invoke(records, ["show", str(record.id)])

    assert result.exit_code == 0
    assert "Records" in result.output
    assert record.label in result.output


def test_records_show_not_found(sample_db_with_records, cli_runner):
    """Test showing a non-existent record."""
    result = cli_runner.invoke(records, ["show", "999999"])

    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_records_show_json(sample_db_with_records, cli_runner):
    """Test showing record in JSON format."""
    # Get first record
    session = sample_db_with_records
    record = session.query(Record).first()

    result = cli_runner.invoke(records, ["show", str(record.id), "--format", "json"])

    assert result.exit_code == 0
    # Check for valid JSON
    try:
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["label"] == record.label
    except json.JSONDecodeError:
        assert False, "Output is not valid JSON"


def test_records_combined_filters(sample_db_with_records, cli_runner):
    """Test combining multiple filters."""
    # Combine category and amount filters
    result = cli_runner.invoke(
        records, ["list", "--category", "Groceries", "--amount", "50..100"]
    )

    assert result.exit_code == 0
    assert "Records" in result.output


def test_records_invalid_month_format(sample_db_with_records, cli_runner):
    """Test invalid month format produces helpful error."""
    result = cli_runner.invoke(records, ["list", "--month", "invalid"])

    assert result.exit_code != 0
    assert "Invalid month format" in result.output


def test_records_invalid_amount_range(sample_db_with_records, cli_runner):
    """Test invalid amount range produces helpful error."""
    result = cli_runner.invoke(records, ["list", "--amount", "invalid"])

    assert result.exit_code != 0
    assert "Invalid amount range" in result.output


# ---------- Batch Import Tests (CLI-10) ---------- #


def test_add_from_yaml(sample_db_with_records, cli_runner, tmp_path):
    """Test batch import from valid YAML file (list format)."""
    import yaml

    # Get existing account and category slugs
    session = sample_db_with_records
    account = session.query(Account).first()
    category = session.query(Category).first()

    # Create test YAML file (list format)
    yaml_data = [
        {
            "label": "Test Record 1",
            "amount": 100.50,
            "date": "2026-03-15",
            "accountSlug": account.slug,
            "categorySlug": category.slug,
        },
        {
            "label": "Test Record 2",
            "amount": 250.00,
            "date": "2026-03-16",
            "accountSlug": account.slug,
        },
    ]

    yaml_file = tmp_path / "test_records.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(yaml_data, f)

    # Run import command
    with patch("bagels.cli.records.Session", return_value=sample_db_with_records):
        result = cli_runner.invoke(records, ["add", "--yaml", str(yaml_file)])

    assert result.exit_code == 0
    assert "Import complete!" in result.output
    assert "Imported: 2 record(s)" in result.output


def test_add_from_yaml_dict_format(sample_db_with_records, cli_runner, tmp_path):
    """Test batch import from YAML file (dict with records key)."""
    import yaml

    # Get existing account slug
    session = sample_db_with_records
    account = session.query(Account).first()

    # Create test YAML file (dict format with records key)
    yaml_data = {
        "records": [
            {
                "label": "Test Record 3",
                "amount": 75.25,
                "date": "2026-03-17",
                "accountSlug": account.slug,
            }
        ]
    }

    yaml_file = tmp_path / "test_records_dict.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(yaml_data, f)

    # Run import command
    result = cli_runner.invoke(records, ["add", "--yaml", str(yaml_file)])

    assert result.exit_code == 0
    assert "Import complete!" in result.output
    assert "Imported: 1 record(s)" in result.output


def test_add_from_yaml_validation(sample_db_with_records, cli_runner, tmp_path):
    """Test validation errors display for invalid YAML data."""
    import yaml

    # Create test YAML file with missing required fields
    yaml_data = [
        {
            "label": "Invalid Record 1",
            # Missing 'amount' and 'date'
        },
        {
            "amount": 50.00,
            # Missing 'label' and 'date'
        },
        {
            "label": "Invalid Record 3",
            "amount": 30.00,
            "date": "invalid-date",  # Invalid date format
        },
    ]

    yaml_file = tmp_path / "test_invalid_records.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(yaml_data, f)

    # Run import command
    result = cli_runner.invoke(records, ["add", "--yaml", str(yaml_file)])

    # Should fail validation
    assert result.exit_code != 0
    assert (
        "Validation failed" in result.output
        or "Missing required fields" in result.output
    )


def test_add_from_yaml_missing_fields(sample_db_with_records, cli_runner, tmp_path):
    """Test missing required fields are caught."""
    import yaml

    # Create test YAML file with missing label
    yaml_data = [
        {
            "amount": 100.00,
            "date": "2026-03-15",
            # Missing 'label'
        }
    ]

    yaml_file = tmp_path / "test_missing_label.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(yaml_data, f)

    # Run import command
    result = cli_runner.invoke(records, ["add", "--yaml", str(yaml_file)])

    assert result.exit_code != 0
    assert "Missing required fields" in result.output or "label" in result.output


def test_add_from_yaml_invalid_date(sample_db_with_records, cli_runner, tmp_path):
    """Test invalid date format is caught."""
    import yaml

    # Get existing account slug
    session = sample_db_with_records
    account = session.query(Account).first()

    # Create test YAML file with invalid date
    yaml_data = [
        {
            "label": "Test Record",
            "amount": 100.00,
            "date": "15-03-2026",  # Wrong format (should be YYYY-MM-DD)
            "accountSlug": account.slug,
        }
    ]

    yaml_file = tmp_path / "test_invalid_date.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(yaml_data, f)

    # Run import command
    result = cli_runner.invoke(records, ["add", "--yaml", str(yaml_file)])

    assert result.exit_code != 0
    assert "Invalid date format" in result.output


def test_add_from_yaml_foreign_keys(sample_db_with_records, cli_runner, tmp_path):
    """Test foreign key resolution (accountSlug, categorySlug)."""
    import yaml

    # Get existing account and category slugs
    session = sample_db_with_records
    account = session.query(Account).first()
    category = session.query(Category).first()

    # Count records before import
    records_before = session.query(Record).count()

    # Create test YAML file with foreign keys
    yaml_data = [
        {
            "label": "Test with FKs",
            "amount": 150.00,
            "date": "2026-03-18",
            "accountSlug": account.slug,
            "categorySlug": category.slug,
        }
    ]

    yaml_file = tmp_path / "test_fks.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(yaml_data, f)

    # Run import command
    result = cli_runner.invoke(records, ["add", "--yaml", str(yaml_file)])

    assert result.exit_code == 0
    assert "Import complete!" in result.output

    # Verify record was created with correct foreign keys
    records_after = session.query(Record).count()
    assert records_after == records_before + 1

    new_record = session.query(Record).filter(Record.label == "Test with FKs").first()
    assert new_record is not None
    assert new_record.accountId == account.id
    assert new_record.categoryId == category.id


def test_add_from_yaml_invalid_fk(sample_db_with_records, cli_runner, tmp_path):
    """Test error on non-existent foreign keys."""
    import yaml

    # Create test YAML file with non-existent account
    yaml_data = [
        {
            "label": "Test with Invalid FK",
            "amount": 100.00,
            "date": "2026-03-19",
            "accountSlug": "non-existent-account",
        }
    ]

    yaml_file = tmp_path / "test_invalid_fk.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(yaml_data, f)

    # Run import command
    result = cli_runner.invoke(records, ["add", "--yaml", str(yaml_file)])

    assert result.exit_code != 0
    assert "not found" in result.output


def test_add_from_yaml_empty(sample_db_with_records, cli_runner, tmp_path):
    """Test handles empty YAML gracefully."""
    import yaml

    # Create empty YAML file
    yaml_file = tmp_path / "test_empty.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump([], f)

    # Run import command
    result = cli_runner.invoke(records, ["add", "--yaml", str(yaml_file)])

    assert result.exit_code == 0
    assert "No records found" in result.output


def test_add_from_yaml_multiple(sample_db_with_records, cli_runner, tmp_path):
    """Test importing multiple records at once."""
    import yaml

    # Get existing account slug
    session = sample_db_with_records
    account = session.query(Account).first()

    # Count records before import
    records_before = session.query(Record).count()

    # Create test YAML file with multiple records
    yaml_data = [
        {
            "label": f"Test Record {i}",
            "amount": float(10 * i),
            "date": "2026-03-20",
            "accountSlug": account.slug,
        }
        for i in range(1, 6)
    ]

    yaml_file = tmp_path / "test_multiple.yaml"
    with open(yaml_file, "w") as f:
        yaml.dump(yaml_data, f)

    # Run import command
    result = cli_runner.invoke(records, ["add", "--yaml", str(yaml_file)])

    assert result.exit_code == 0
    assert "Import complete!" in result.output
    assert "Imported: 5 record(s)" in result.output

    # Verify all records were created
    records_after = session.query(Record).count()
    assert records_after == records_before + 5
