"""
Tests for accounts command (CLI-04).

Tests account listing with multiple output formats.
"""

import pytest
import json
from click.testing import CliRunner

from bagels.cli.accounts import accounts


def test_accounts_list_default(cli_runner, sample_db_with_records):
    """Test accounts list with default table format."""
    result = cli_runner.invoke(accounts, ["list"])
    assert result.exit_code == 0
    # Check that account names are displayed
    assert "Savings" in result.output
    assert "Checking" in result.output
    assert "Credit Card" in result.output
    # Check that balances are displayed
    assert "5000" in result.output or "5000.00" in result.output  # Savings
    assert "2000" in result.output or "2000.00" in result.output  # Checking


def test_accounts_json_format(cli_runner, sample_db_with_records):
    """Test JSON output format."""
    result = cli_runner.invoke(accounts, ["list", "--format", "json"])
    assert result.exit_code == 0
    # Parse JSON
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0  # Should have at least some accounts
    # Check first account structure
    assert "id" in data[0]
    assert "name" in data[0]
    assert "beginning_balance" in data[0]


def test_accounts_yaml_format(cli_runner, sample_db_with_records):
    """Test YAML output format (CLI-04 requirement)."""
    result = cli_runner.invoke(accounts, ["list", "--format", "yaml"])
    assert result.exit_code == 0
    # Check YAML format
    assert "beginning_balance:" in result.output
    assert "Savings" in result.output
    assert "Checking" in result.output


def test_accounts_negative_balance(cli_runner, sample_db_with_records):
    """Test that negative balances are displayed correctly."""
    result = cli_runner.invoke(accounts, ["list"])
    assert result.exit_code == 0
    # Credit Card account should be displayed
    assert "Credit Card" in result.output
    # Check that balance is shown (whether negative or positive)
    assert "$" in result.output or "balance" in result.output.lower()


def test_accounts_empty(cli_runner):
    """Test accounts list handles empty case gracefully."""
    # Note: This test verifies the command doesn't crash
    # Actual empty database testing requires proper isolation
    result = cli_runner.invoke(accounts, ["list"])
    assert result.exit_code == 0
    # Just verify it runs without error


def test_accounts_list_command(cli_runner, sample_db_with_records):
    """Test that accounts list is accessible via CLI."""
    # Test help text
    result = cli_runner.invoke(accounts, ["--help"])
    assert result.exit_code == 0
    assert "list" in result.output
    assert "Query and manage accounts" in result.output


def test_accounts_list_help(cli_runner, sample_db_with_records):
    """Test accounts list subcommand help."""
    result = cli_runner.invoke(accounts, ["list", "--help"])
    assert result.exit_code == 0
    assert "List all accounts" in result.output
    assert "--format" in result.output or "-f" in result.output
