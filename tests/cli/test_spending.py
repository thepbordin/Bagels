"""
Tests for spending commands (CLI-06, CLI-07).
"""

import pytest
import json
from click.testing import CliRunner
from bagels.cli.spending import spending


def test_spending_by_category(cli_runner, sample_db_with_records):
    """Test spending breakdown by category."""
    result = cli_runner.invoke(spending, ["by-category"])
    assert result.exit_code == 0
    # Check that categories are displayed
    assert "Spending by Category" in result.output
    # The test data creates hierarchical categories, so we should see at least one category
    assert (
        "Food" in result.output
        or "Transport" in result.output
        or "Entertainment" in result.output
    )
    # Check for amount column
    assert "$" in result.output


def test_spending_by_category_month(cli_runner, sample_db_with_records):
    """Test --month flag."""
    result = cli_runner.invoke(spending, ["by-category", "--month", "2026-03"])
    assert result.exit_code == 0
    assert "Spending by Category" in result.output
    assert "2026-03" in result.output


def test_spending_by_day(cli_runner, sample_db_with_records):
    """Test daily spending breakdown."""
    result = cli_runner.invoke(spending, ["by-day"])
    assert result.exit_code == 0
    assert "Daily Spending" in result.output
    # Check for dates and amounts
    assert "$" in result.output
    # Should have AVERAGE row
    assert "AVERAGE" in result.output


def test_spending_by_day_month(cli_runner, sample_db_with_records):
    """Test --month flag for daily spending."""
    result = cli_runner.invoke(spending, ["by-day", "--month", "2026-03"])
    assert result.exit_code == 0
    assert "Daily Spending" in result.output
    assert "2026-03" in result.output


def test_spending_by_category_json(cli_runner, sample_db_with_records):
    """Test JSON output for spending by category."""
    result = cli_runner.invoke(spending, ["by-category", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "month" in data
    assert "total" in data
    assert "categories" in data
    assert isinstance(data["categories"], list)


def test_spending_by_day_json(cli_runner, sample_db_with_records):
    """Test JSON output for daily spending."""
    result = cli_runner.invoke(spending, ["by-day", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "month" in data
    assert "total" in data
    assert "daily_average" in data
    assert "days" in data
    assert isinstance(data["days"], list)


def test_spending_by_category_yaml(cli_runner, sample_db_with_records):
    """Test YAML output for spending by category."""
    result = cli_runner.invoke(spending, ["by-category", "--format", "yaml"])
    assert result.exit_code == 0
    # Check that YAML contains expected content
    assert "month:" in result.output
    assert "total:" in result.output
    assert "categories:" in result.output


def test_spending_by_day_yaml(cli_runner, sample_db_with_records):
    """Test YAML output for daily spending."""
    result = cli_runner.invoke(spending, ["by-day", "--format", "yaml"])
    assert result.exit_code == 0
    # Check that YAML contains expected content
    assert "month:" in result.output
    assert "total:" in result.output
    assert "days:" in result.output
    assert "daily_average:" in result.output


def test_spending_no_data(cli_runner):
    """Test handles empty month gracefully."""
    result = cli_runner.invoke(spending, ["by-category", "--month", "2099-01"])
    assert result.exit_code == 0
    # Should show "No spending data" message
    assert "No spending data" in result.output
