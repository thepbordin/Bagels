"""
Tests for categories command (CLI-05).
"""

import pytest
import json
from click.testing import CliRunner
from bagels.cli.categories import categories


def test_categories_tree(cli_runner, sample_db_with_records):
    """Test category tree display."""
    result = cli_runner.invoke(categories, ["tree"])
    assert result.exit_code == 0
    # Check that categories are displayed
    assert "Food" in result.output
    assert "Groceries" in result.output
    assert "Restaurants" in result.output
    assert "Transport" in result.output
    assert "Entertainment" in result.output


def test_categories_tree_json(cli_runner, sample_db_with_records):
    """Test JSON output format."""
    result = cli_runner.invoke(categories, ["tree", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) > 0
    # Check structure
    assert "id" in data[0]
    assert "name" in data[0]
    assert "nature" in data[0]
    assert "color" in data[0]
    assert "depth" in data[0]


def test_categories_tree_yaml(cli_runner, sample_db_with_records):
    """Test YAML output format."""
    result = cli_runner.invoke(categories, ["tree", "--format", "yaml"])
    assert result.exit_code == 0
    # Check that YAML contains expected content
    assert "Food" in result.output
    assert "Groceries" in result.output
    assert "nature:" in result.output
    assert "color:" in result.output


def test_categories_nested(cli_runner, sample_db_with_records):
    """Test parent-child relationships display correctly."""
    result = cli_runner.invoke(categories, ["tree"])
    assert result.exit_code == 0
    # In tree format, child categories should appear after parent
    lines = result.output.split("\n")
    food_line_idx = None
    groceries_line_idx = None

    for i, line in enumerate(lines):
        if "Food" in line and "●" in line:
            food_line_idx = i
        if "Groceries" in line and ("├" in line or "└" in line):
            groceries_line_idx = i

    # Food should appear before Groceries
    assert food_line_idx is not None
    assert groceries_line_idx is not None
    assert food_line_idx < groceries_line_idx


def test_categories_empty(cli_runner):
    """Test handles no categories gracefully."""
    result = cli_runner.invoke(categories, ["tree"])
    assert result.exit_code == 0
    # Should show "No categories found" or similar message
    assert "No categories" in result.output or "Category Tree" in result.output
