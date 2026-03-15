"""
Tests for summary command (CLI-03).

Tests financial summary display including income, expenses, and savings.
"""

import pytest
import json
from click.testing import CliRunner

from bagels.cli.summary import summary


def test_summary_default_month(cli_runner, sample_db_with_records):
    """Test summary for current month (March 2026)."""
    result = cli_runner.invoke(summary, [])
    assert result.exit_code == 0
    # Check that key metrics are displayed
    assert "income" in result.output.lower() or "total_income" in result.output.lower()
    assert (
        "expense" in result.output.lower()
        or "total_expenses" in result.output.lower()
        or "expenses" in result.output.lower()
    )
    assert "saving" in result.output.lower() or "net_savings" in result.output.lower()


def test_summary_specific_month(cli_runner, sample_db_with_records):
    """Test summary for specific month."""
    # Get current date to calculate a valid month
    from datetime import datetime

    now = datetime.now()
    # Test with a month that has data (previous month)
    prev_month = now.month - 1 if now.month > 1 else 12
    prev_year = now.year if now.month > 1 else now.year - 1
    month_str = f"{prev_year:04d}-{prev_month:02d}"

    result = cli_runner.invoke(summary, ["--month", month_str])
    assert result.exit_code == 0
    # Check that month is displayed
    assert month_str in result.output


def test_summary_json_format(cli_runner, sample_db_with_records):
    """Test JSON output format."""
    result = cli_runner.invoke(summary, ["--format", "json"])
    assert result.exit_code == 0
    # Parse JSON
    data = json.loads(result.output)
    assert "month" in data
    assert "total_income" in data
    assert "total_expenses" in data
    assert "net_savings" in data
    assert "record_count" in data
    # Verify data types
    assert isinstance(data["total_income"], (int, float))
    assert isinstance(data["total_expenses"], (int, float))
    assert isinstance(data["net_savings"], (int, float))
    assert isinstance(data["record_count"], int)


def test_summary_yaml_format(cli_runner, sample_db_with_records):
    """Test YAML output format."""
    result = cli_runner.invoke(summary, ["--format", "yaml"])
    assert result.exit_code == 0
    # Check YAML format
    assert "month:" in result.output
    assert "total_income:" in result.output
    assert "total_expenses:" in result.output
    assert "net_savings:" in result.output


def test_calculate_monthly_summary(sample_db_with_records):
    """Test calculation logic directly."""
    from bagels.queries.summaries import calculate_monthly_summary
    from datetime import datetime

    # Get current date to calculate a valid month
    now = datetime.now()
    prev_month = now.month - 1 if now.month > 1 else 12
    prev_year = now.year if now.month > 1 else now.year - 1
    month_str = f"{prev_year:04d}-{prev_month:02d}"

    summary_data = calculate_monthly_summary(sample_db_with_records, month_str)
    assert summary_data["month"] == month_str
    assert isinstance(summary_data["total_income"], (int, float))
    assert isinstance(summary_data["total_expenses"], (int, float))
    assert isinstance(summary_data["net_savings"], (int, float))
    assert isinstance(summary_data["record_count"], int)


def test_calculate_budget_status(sample_db_with_records):
    """Test budget status calculation."""
    from bagels.queries.summaries import calculate_budget_status

    # First, add budgets to some categories
    from bagels.models.category import Category

    categories = sample_db_with_records.query(Category).all()
    if categories:
        # Add budget to first category
        categories[0].monthlyBudget = 500.0
        sample_db_with_records.commit()

        budget_data = calculate_budget_status(sample_db_with_records, "2026-01")
        assert "month" in budget_data
        assert "categories" in budget_data
        assert isinstance(budget_data["categories"], list)


def test_summary_no_records(cli_runner):
    """Test summary with empty database."""
    # Use a fresh session with no records
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from bagels.models.database.db import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    result = cli_runner.invoke(summary, ["--month", "2026-01"])
    assert result.exit_code == 0
    # Should show zero values
    assert "0" in result.output

    session.close()
