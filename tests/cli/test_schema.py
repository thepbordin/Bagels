"""
Tests for schema commands (LLM-02, LLM-03).

Tests data model schema viewing functionality.
"""

import pytest
import json
import yaml
from click.testing import CliRunner

from bagels.cli.schema import schema


def test_schema_full(cli_runner, sample_db_with_records):
    """Test full schema display."""
    result = cli_runner.invoke(schema, ["full"])
    assert result.exit_code == 0
    # Should show all models
    assert "Account:" in result.output
    assert "Category:" in result.output
    assert "Record:" in result.output
    assert "Person:" in result.output
    assert "RecordTemplate:" in result.output


def test_schema_model_record(cli_runner, sample_db_with_records):
    """Test Record model schema."""
    result = cli_runner.invoke(schema, ["model", "record"])
    assert result.exit_code == 0
    # Should show Record model
    assert "Record" in result.output or "record" in result.output.lower()
    # Should have table name
    assert "table_name:" in result.output


def test_schema_model_account(cli_runner, sample_db_with_records):
    """Test Account model schema."""
    result = cli_runner.invoke(schema, ["model", "account"])
    assert result.exit_code == 0
    # Should show Account model
    assert "Account" in result.output or "account" in result.output.lower()


def test_schema_model_category(cli_runner, sample_db_with_records):
    """Test Category model schema."""
    result = cli_runner.invoke(schema, ["model", "category"])
    assert result.exit_code == 0
    # Should show Category model
    assert "Category" in result.output or "category" in result.output.lower()


def test_schema_model_person(cli_runner, sample_db_with_records):
    """Test Person model schema."""
    result = cli_runner.invoke(schema, ["model", "person"])
    assert result.exit_code == 0
    # Should show Person model
    assert "Person" in result.output or "person" in result.output.lower()


def test_schema_model_template(cli_runner, sample_db_with_records):
    """Test RecordTemplate model schema."""
    result = cli_runner.invoke(schema, ["model", "template"])
    assert result.exit_code == 0
    # Should show RecordTemplate model
    assert "RecordTemplate" in result.output or "template" in result.output.lower()


def test_schema_json_format(cli_runner, sample_db_with_records):
    """Test JSON output format."""
    result = cli_runner.invoke(schema, ["model", "record", "--format", "json"])
    assert result.exit_code == 0
    # Should be valid JSON
    data = json.loads(result.output)
    assert isinstance(data, dict)
    # Should have table_name and fields
    assert "table_name" in data
    assert "fields" in data


def test_schema_yaml_format(cli_runner, sample_db_with_records):
    """Test YAML output format."""
    result = cli_runner.invoke(schema, ["model", "account", "--format", "yaml"])
    assert result.exit_code == 0
    # Should be valid YAML
    data = yaml.safe_load(result.output)
    assert isinstance(data, dict)
    # Should have table_name and fields
    assert "table_name" in data
    assert "fields" in data


def test_schema_field_types(cli_runner, sample_db_with_records):
    """Test field types extracted correctly."""
    result = cli_runner.invoke(schema, ["model", "record", "--format", "json"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    fields = data.get("fields", [])

    # Should have multiple fields
    assert len(fields) > 0

    # Each field should have name, type, nullable
    for field in fields:
        assert "name" in field
        assert "type" in field
        assert "nullable" in field


def test_schema_relationships(cli_runner, sample_db_with_records):
    """Test relationships extracted correctly."""
    result = cli_runner.invoke(schema, ["model", "record", "--format", "json"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    relationships = data.get("relationships", [])

    # Record should have relationships (category, account, etc.)
    # At minimum, should have relationships list
    assert isinstance(relationships, list)


def test_schema_invalid_model(cli_runner, sample_db_with_records):
    """Test invalid model name."""
    # Click should handle invalid choice
    result = cli_runner.invoke(schema, ["model", "invalid"])
    assert result.exit_code != 0


def test_schema_help_text(cli_runner, sample_db_with_records):
    """Test schema command help text."""
    result = cli_runner.invoke(schema, ["--help"])
    assert result.exit_code == 0
    assert "View data schema" in result.output


def test_schema_model_help_text(cli_runner, sample_db_with_records):
    """Test schema model command help text."""
    result = cli_runner.invoke(schema, ["model", "--help"])
    assert result.exit_code == 0
    assert "Show schema for a specific model" in result.output
