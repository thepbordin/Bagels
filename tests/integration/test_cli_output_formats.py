"""
Integration tests for CLI output format correctness (TEST-03).

Validates that structured output formats (JSON, YAML, table) are parseable
and contain expected keys for records, accounts, and schema commands.
"""

import json
import pytest
import yaml
from unittest.mock import patch

from bagels.cli.records import records
from bagels.cli.accounts import accounts
from bagels.cli.schema import schema


class TestRecordsOutputFormats:
    """Tests for bagels records list output formats."""

    def test_records_list_table_format(self, cli_runner, sample_cli_db):
        """Table format should exit cleanly and include column headers."""
        with patch("bagels.cli.records.Session", return_value=sample_cli_db):
            result = cli_runner.invoke(records, ["list"])

        assert result.exit_code == 0, f"Unexpected output: {result.output}"
        output_lower = result.output.lower()
        # Table headers should appear (rich table may capitalise differently)
        assert "label" in output_lower or "record" in output_lower, (
            f"Expected table header in output. Got: {result.output[:300]}"
        )

    def test_records_list_json_format(self, cli_runner, sample_cli_db):
        """JSON format must produce valid, non-empty JSON with expected keys."""
        with patch("bagels.cli.records.Session", return_value=sample_cli_db):
            # Use --month filter to stay within sample data and avoid the
            # "Showing N most recent records" warning that prefixes the output
            result = cli_runner.invoke(
                records, ["list", "--format", "json", "--month", "2026-03"]
            )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Strip any leading warning lines (lines that don't start with '[' or '{')
        output_lines = result.output.strip().splitlines()
        json_start = next(
            (
                i
                for i, line in enumerate(output_lines)
                if line.lstrip().startswith(("[", "{"))
            ),
            0,
        )
        json_text = "\n".join(output_lines[json_start:])

        # Must be parseable JSON
        parsed = json.loads(json_text)

        # Determine structure: list of records, or dict with a "records" key
        if isinstance(parsed, list):
            assert len(parsed) > 0, "Expected at least one record in JSON output"
            first = parsed[0]
        elif isinstance(parsed, dict):
            key = next(
                (k for k in ("records", "data") if k in parsed),
                None,
            )
            assert key is not None, (
                f"Expected 'records' key in dict output. Keys: {list(parsed.keys())}"
            )
            assert len(parsed[key]) > 0
            first = parsed[key][0]
        else:
            pytest.fail(f"Unexpected JSON root type: {type(parsed)}")

        # At least one of these identifying keys must be present
        assert "label" in first or "amount" in first, (
            f"Expected 'label' or 'amount' in record. Got keys: {list(first.keys())}"
        )

    def test_records_list_yaml_format(self, cli_runner, sample_cli_db):
        """YAML format must produce valid, parseable YAML."""
        with patch("bagels.cli.records.Session", return_value=sample_cli_db):
            # Use --month filter to stay within sample data and avoid the
            # "Showing N most recent records" warning that prefixes the output
            result = cli_runner.invoke(
                records, ["list", "--format", "yaml", "--month", "2026-03"]
            )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Strip any leading warning lines before the YAML content
        # YAML list starts with '- ' and YAML dict starts with key:
        output = result.output.strip()
        yaml_start = output.find("- ")
        if yaml_start > 0:
            output = output[yaml_start:]

        # Must be parseable YAML
        parsed = yaml.safe_load(output)
        assert parsed is not None, "YAML output parsed to None"

    def test_accounts_list_json_format(self, cli_runner, sample_cli_db):
        """accounts list --format json must produce valid JSON with account data."""
        with patch("bagels.cli.accounts.Session", return_value=sample_cli_db):
            result = cli_runner.invoke(accounts, ["list", "--format", "json"])

        assert result.exit_code == 0, f"Command failed: {result.output}"

        parsed = json.loads(result.output)

        if isinstance(parsed, list):
            assert len(parsed) > 0
        elif isinstance(parsed, dict):
            # Could be {"accounts": [...]} or similar
            assert any(isinstance(v, list) and len(v) > 0 for v in parsed.values()), (
                f"Expected non-empty list value in dict. Got: {parsed}"
            )
        else:
            pytest.fail(f"Unexpected JSON root type: {type(parsed)}")

    def test_accounts_list_yaml_format(self, cli_runner, sample_cli_db):
        """accounts list --format yaml must produce valid, non-None YAML."""
        with patch("bagels.cli.accounts.Session", return_value=sample_cli_db):
            result = cli_runner.invoke(accounts, ["list", "--format", "yaml"])

        assert result.exit_code == 0, f"Command failed: {result.output}"

        parsed = yaml.safe_load(result.output)
        assert parsed is not None, "YAML output parsed to None"

    def test_schema_full_command_produces_output(self, cli_runner, sample_cli_db):
        """schema full should exit 0 and produce non-empty output."""
        result = cli_runner.invoke(schema, ["full"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert len(result.output.strip()) > 0, "Schema output was empty"

    def test_schema_model_record_command_produces_output(
        self, cli_runner, sample_cli_db
    ):
        """schema model record should include record/slug keywords in output."""
        result = cli_runner.invoke(schema, ["model", "record"])

        assert result.exit_code == 0, f"Command failed: {result.output}"
        output_lower = result.output.lower()
        assert "record" in output_lower or "slug" in output_lower, (
            f"Expected 'record' or 'slug' in output. Got: {result.output[:300]}"
        )
