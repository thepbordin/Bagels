"""
Tests for trends command (CLI-08).

Tests month-over-month spending comparison and category trends.
"""

import pytest
import json
from click.testing import CliRunner

from bagels.cli.trends import trends


def test_trends_default_months(cli_runner, sample_db_with_records):
    """Test 3-month comparison (default)."""
    result = cli_runner.invoke(trends, [])
    assert result.exit_code == 0
    # Should show table header
    assert "Monthly Spending Comparison" in result.output
    # Should have month column
    assert "Month" in result.output
    # Should have change column
    assert "Change" in result.output


def test_trends_custom_months(cli_runner, sample_db_with_records):
    """Test custom month range."""
    result = cli_runner.invoke(trends, ["--months", "6"])
    assert result.exit_code == 0
    # Should show table
    assert "Monthly Spending Comparison" in result.output


def test_trends_category_filter(cli_runner, sample_db_with_records):
    """Test --category filter."""
    result = cli_runner.invoke(trends, ["--category", "Food"])
    # Since "Food" is a parent category, it may not have direct records
    # The command should handle this gracefully
    assert result.exit_code == 0 or "not found" in result.output.lower()


def test_trends_json_format(cli_runner, sample_db_with_records):
    """Test JSON output format."""
    result = cli_runner.invoke(trends, ["--format", "json"])
    assert result.exit_code == 0
    # Should be valid JSON
    data = json.loads(result.output)
    assert isinstance(data, list)
    # Each month should have summary data
    if len(data) > 0:
        assert "month" in data[0]
        assert "total_income" in data[0]
        assert "total_expenses" in data[0]
        assert "net_savings" in data[0]


def test_trends_yaml_format(cli_runner, sample_db_with_records):
    """Test YAML output format."""
    result = cli_runner.invoke(trends, ["--format", "yaml"])
    assert result.exit_code == 0
    # Should contain YAML-like structure
    assert "month:" in result.output or "- month:" in result.output


def test_trends_invalid_months(cli_runner, sample_db_with_records):
    """Test invalid months parameter."""
    result = cli_runner.invoke(trends, ["--months", "15"])
    assert result.exit_code == 0
    assert "must be between 1 and 12" in result.output


def test_trends_month_over_month_calculation(cli_runner, sample_db_with_records):
    """Test month-over-month change calculation."""
    result = cli_runner.invoke(trends, ["--months", "2"])
    assert result.exit_code == 0
    # Should show change indicators
    output = result.output
    # May contain arrows if there's data with changes
    has_arrows = "↑" in output or "↓" in output or "→" in output
    # At minimum should have N/A for most recent month
    assert "N/A" in output or has_arrows
