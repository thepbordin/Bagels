"""
Tests for LLM commands (LLM-01, LLM-04, LLM-05).

Tests LLM context dump functionality.
"""

import pytest
import json
import yaml
from click.testing import CliRunner

from bagels.cli.llm import llm


def test_llm_context_month(cli_runner, sample_db_with_records):
    """Test LLM context dump for current month."""
    result = cli_runner.invoke(llm, ["context"])
    assert result.exit_code == 0
    # Should output YAML with accounts, summary, spending, records, budget
    assert "accounts:" in result.output or "accounts:" in result.output.lower()
    assert "summary:" in result.output or "summary:" in result.output.lower()


def test_context_completeness(cli_runner, sample_db_with_records):
    """Test all sections present in context."""
    result = cli_runner.invoke(llm, ["context"])
    assert result.exit_code == 0

    # Parse YAML output
    data = yaml.safe_load(result.output)

    # Verify required sections
    assert "accounts" in data or "accounts" in data
    assert "summary" in data or "summary" in data
    assert "spending_by_category" in data or "spending_by_category" in data
    assert "recent_records" in data or "recent_records" in data
    assert "categories" in data or "categories" in data


def test_context_budget_status(cli_runner, sample_db_with_records):
    """Test budget progress included in context."""
    result = cli_runner.invoke(llm, ["context"])
    assert result.exit_code == 0

    # Parse YAML output
    data = yaml.safe_load(result.output)

    # Budget status may be None if no budgets set
    # Just verify the field exists
    assert "budget_status" in data or "budget_status" in data


def test_context_specific_month(cli_runner, sample_db_with_records):
    """Test context for specific month."""
    # Use a month that likely has data
    result = cli_runner.invoke(llm, ["context", "--month", "2026-01"])
    assert result.exit_code == 0

    # Parse YAML output
    data = yaml.safe_load(result.output)

    # Verify period is set
    assert "period" in data
    assert "2026-01" in str(data["period"])


def test_context_period_option(cli_runner, sample_db_with_records):
    """Test --period option."""
    result = cli_runner.invoke(llm, ["context", "--period", "30d"])
    assert result.exit_code == 0

    # Parse YAML output
    data = yaml.safe_load(result.output)

    # Verify period is set
    assert "period" in data
    assert "30d" in str(data["period"])


def test_context_days_option(cli_runner, sample_db_with_records):
    """Test --days option."""
    result = cli_runner.invoke(llm, ["context", "--days", "60"])
    assert result.exit_code == 0

    # Parse YAML output
    data = yaml.safe_load(result.output)

    # Verify period is set
    assert "period" in data
    assert "60" in str(data["period"])


def test_context_yaml_valid(cli_runner, sample_db_with_records):
    """Test output is valid YAML."""
    result = cli_runner.invoke(llm, ["context"])
    assert result.exit_code == 0

    # Should be valid YAML
    try:
        data = yaml.safe_load(result.output)
        assert isinstance(data, dict)
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML output: {e}")


def test_context_mutually_exclusive_options(cli_runner, sample_db_with_records):
    """Test that --month, --period, and --days are mutually exclusive."""
    result = cli_runner.invoke(llm, ["context", "--month", "2026-01", "--days", "30"])
    assert result.exit_code == 0
    assert "only one" in result.output.lower()


def test_llm_help_text(cli_runner, sample_db_with_records):
    """Test LLM command help text."""
    result = cli_runner.invoke(llm, ["--help"])
    assert result.exit_code == 0
    assert "LLM integration commands" in result.output
    assert "context" in result.output


def test_llm_context_help_text(cli_runner, sample_db_with_records):
    """Test llm context command help text."""
    result = cli_runner.invoke(llm, ["context", "--help"])
    assert result.exit_code == 0
    assert "Dump financial snapshot" in result.output
