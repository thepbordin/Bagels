"""
Integration tests for records query commands.

Tests the bagels records list and show commands with various filters
and output formats.
"""

import json
from click.testing import CliRunner
from bagels.models.record import Record
from bagels.models.category import Category
from bagels.models.account import Account
from bagels.cli.records import records


def test_records_list_default(sample_db_with_records, cli_runner):
    """Test listing records without filters (table format)."""
    result = cli_runner.invoke(records, ["list"])

    assert result.exit_code == 0
    assert "Records" in result.output
    # Check for table headers
    assert "ID" in result.output
    assert "Date" in result.output
    assert "Label" in result.output
    assert "Amount" in result.output
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
