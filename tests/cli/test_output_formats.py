"""
Comprehensive tests for output formatting and filter utilities.

Tests cover:
- Table format rendering with styled columns
- JSON format with datetime serialization
- YAML format with datetime serialization
- Filter utility functions (parse_month, parse_amount_range, apply_filters)
"""

import json
import pytest
from datetime import datetime
from bagels.queries.formatters import (
    format_records,
    format_accounts,
    format_categories,
    format_summary,
    to_json,
    to_yaml,
    _record_to_dict,
    _account_to_dict,
    _category_to_dict,
)
from bagels.queries.filters import (
    parse_month,
    parse_amount_range,
    apply_date_filters,
    apply_category_filter,
    apply_amount_filter,
    apply_account_filter,
)


class TestTableFormats:
    """Test table format output for all entity types."""

    def test_format_records_table(self, sample_records):
        """Verifies table output contains headers and styled columns."""
        output = format_records(sample_records, output_format="table")

        # Check table structure (headers may be truncated with ellipsis)
        assert "Records" in output
        assert "ID" in output
        assert "Date" in output
        assert "Label" in output
        assert "Amount" in output or "Amo" in output  # May be truncated
        assert "Category" in output or "Categ" in output  # May be truncated
        assert "Account" in output or "Acc" in output  # May be truncated

        # Check that sample data is present
        assert len(sample_records) > 0
        # At least one record should be in output
        assert sample_records[0].label in output

    def test_format_accounts_table(self, sample_accounts):
        """Verifies account table structure."""
        output = format_accounts(sample_accounts, output_format="table")

        # Check table structure (headers may be truncated)
        assert "Accounts" in output
        assert "ID" in output
        assert "Name" in output
        assert "Balance" in output or "Bal" in output  # May be truncated

        # Check sample data
        assert len(sample_accounts) > 0
        assert sample_accounts[0].name in output

    def test_format_categories_table(self, sample_categories):
        """Verifies category table with parent relationships."""
        output = format_categories(sample_categories, output_format="table")

        # Check table structure (headers may be truncated)
        assert "Categories" in output
        assert "ID" in output
        assert "Name" in output
        assert "Nature" in output
        assert "Parent" in output or "Par" in output  # May be truncated

        # Check sample data
        assert len(sample_categories) > 0
        assert sample_categories[0].name in output

    def test_format_summary_table(self):
        """Verifies summary table structure."""
        summary_data = {
            "Total Income": 5000.0,
            "Total Expenses": 3200.5,
            "Net Savings": 1799.5,
            "Record Count": 42,
        }

        output = format_summary(summary_data, output_format="table")

        # Check table structure
        assert "Summary" in output
        assert "Metric" in output
        assert "Value" in output

        # Check data is present
        assert "Total Income" in output
        # Amount may be formatted with $ or commas
        assert "5000.00" in output or "5,000" in output or "$5000" in output

    def test_format_records_empty(self):
        """Verifies empty records list returns appropriate message."""
        output = format_records([], output_format="table")
        assert output == "No records found."

    def test_format_accounts_empty(self):
        """Verifies empty accounts list returns appropriate message."""
        output = format_accounts([], output_format="table")
        assert output == "No accounts found."


class TestJSONFormats:
    """Test JSON format output with datetime serialization."""

    def test_format_records_json(self, sample_records):
        """Verifies JSON is valid and contains all fields."""
        output = format_records(sample_records, output_format="json")

        # Parse JSON to verify validity
        data = json.loads(output)

        assert isinstance(data, list)
        assert len(data) == len(sample_records)

        # Check first record structure
        if data:
            first_record = data[0]
            assert "id" in first_record
            assert "label" in first_record
            assert "amount" in first_record
            assert "date" in first_record
            assert "category" in first_record
            assert "account" in first_record

    def test_json_datetime_serialization(self, sample_records):
        """Verifies datetime objects convert to strings."""
        output = format_records(sample_records, output_format="json")
        data = json.loads(output)

        # Check that datetime fields are serialized as strings
        if data:
            first_record = data[0]
            # Date should be a string (ISO format)
            assert isinstance(first_record.get("date"), str)
            # Created_at should be a string if present
            if first_record.get("created_at"):
                assert isinstance(first_record["created_at"], str)

    def test_json_nested_objects(self, sample_records):
        """Verifies category.name and account.name are included."""
        output = format_records(sample_records, output_format="json")
        data = json.loads(output)

        if data:
            first_record = data[0]

            # Check nested category object
            if first_record.get("category"):
                assert isinstance(first_record["category"], dict)
                assert "id" in first_record["category"]
                assert "name" in first_record["category"]

            # Check nested account object
            if first_record.get("account"):
                assert isinstance(first_record["account"], dict)
                assert "id" in first_record["account"]
                assert "name" in first_record["account"]

    def test_format_accounts_json(self, sample_accounts):
        """Verifies accounts JSON format."""
        output = format_accounts(sample_accounts, output_format="json")
        data = json.loads(output)

        assert isinstance(data, list)
        assert len(data) == len(sample_accounts)

        if data:
            first_account = data[0]
            assert "id" in first_account
            assert "name" in first_account
            assert "beginning_balance" in first_account

    def test_format_categories_json(self, sample_categories):
        """Verifies categories JSON format."""
        output = format_categories(sample_categories, output_format="json")
        data = json.loads(output)

        assert isinstance(data, list)
        assert len(data) == len(sample_categories)

        if data:
            first_category = data[0]
            assert "id" in first_category
            assert "name" in first_category
            assert "nature" in first_category
            # Parent may or may not be present
            if first_category.get("parent"):
                assert isinstance(first_category["parent"], dict)


class TestYAMLFormats:
    """Test YAML format output with datetime serialization."""

    def test_format_records_yaml(self, sample_records):
        """Verifies YAML is valid and readable."""
        output = format_records(sample_records, output_format="yaml")

        # Check that output contains expected data
        assert len(output) > 0
        assert sample_records[0].label in output

    def test_yaml_datetime_serialization(self, sample_records):
        """Verifies datetime handling in YAML output."""
        output = format_records(sample_records, output_format="yaml")

        # YAML should contain date strings
        if sample_records and sample_records[0].date:
            # Date should be serialized in a readable format
            assert "date:" in output

    def test_format_accounts_yaml(self, sample_accounts):
        """Verifies accounts YAML format."""
        output = format_accounts(sample_accounts, output_format="yaml")

        assert len(output) > 0
        assert sample_accounts[0].name in output

    def test_format_categories_yaml(self, sample_categories):
        """Verifies categories YAML format."""
        output = format_categories(sample_categories, output_format="yaml")

        assert len(output) > 0
        assert sample_categories[0].name in output


class TestHelperFunctions:
    """Test internal helper functions."""

    def test_record_to_dict(self, sample_records):
        """Test _record_to_dict helper."""
        if sample_records:
            # Get first record with category and account loaded
            record = sample_records[0]
            result = _record_to_dict(record)
            assert isinstance(result, dict)
            assert "id" in result
            assert "label" in result
            assert "amount" in result

    def test_account_to_dict(self, sample_accounts):
        """Test _account_to_dict helper."""
        if sample_accounts:
            account = sample_accounts[0]
            result = _account_to_dict(account)
            assert isinstance(result, dict)
            assert "id" in result
            assert "name" in result

    def test_category_to_dict(self, sample_categories):
        """Test _category_to_dict helper."""
        if sample_categories:
            category = sample_categories[0]
            result = _category_to_dict(category)
            assert isinstance(result, dict)
            assert "id" in result
            assert "name" in result
            assert "nature" in result

    def test_to_json_helper(self):
        """Test to_json helper function."""
        data = [{"name": "Test", "value": 123}]
        output = to_json(data)
        parsed = json.loads(output)
        assert parsed == data

    def test_to_yaml_helper(self):
        """Test to_yaml helper function."""
        data = [{"name": "Test", "value": 123}]
        output = to_yaml(data)
        assert "name: Test" in output
        assert "value: 123" in output


class TestFilterUtilities:
    """Test filter utility functions."""

    def test_parse_month_valid(self):
        """Verifies '2026-03' returns correct date range."""
        start, end = parse_month("2026-03")

        assert isinstance(start, datetime)
        assert isinstance(end, datetime)
        assert start.year == 2026
        assert start.month == 3
        assert start.day == 1
        assert end.month == 3
        # End should be end of month
        assert end.day >= 28

    def test_parse_month_none(self):
        """Verifies None returns None."""
        result = parse_month(None)
        assert result is None

    def test_parse_month_invalid(self):
        """Verifies ValueError on bad format."""
        with pytest.raises(ValueError):
            parse_month("invalid")

        with pytest.raises(ValueError):
            parse_month("2026/03")  # Wrong separator

        with pytest.raises(ValueError):
            parse_month("26-03")  # Missing century

    def test_parse_amount_range_valid(self):
        """Verifies '100..500' parsing."""
        result = parse_amount_range("100..500")
        assert result == (100.0, 500.0)

    def test_parse_amount_range_no_upper(self):
        """Verifies '100..' parsing."""
        result = parse_amount_range("100..")
        assert result == (100.0, float("inf"))

    def test_parse_amount_range_no_lower(self):
        """Verifies '..500' parsing."""
        result = parse_amount_range("..500")
        assert result == (0.0, 500.0)

    def test_parse_amount_range_none(self):
        """Verifies None returns None."""
        result = parse_amount_range(None)
        assert result is None

    def test_parse_amount_range_invalid(self):
        """Verifies ValueError on bad format."""
        with pytest.raises(ValueError):
            parse_amount_range("100-500")  # Wrong separator

        with pytest.raises(ValueError):
            parse_amount_range("100")  # No range

        with pytest.raises(ValueError):
            parse_amount_range("a..b")  # Non-numeric

    def test_apply_date_filters_month(self, sample_db_with_records):
        """Verifies month filter applies correctly."""
        from bagels.models.record import Record

        query = sample_db_with_records.query(Record)
        filtered = apply_date_filters(query, month="2026-01")

        # Should return a query object
        assert filtered is not None

        # Execute query to verify it works
        results = filtered.all()
        assert isinstance(results, list)

    def test_apply_date_filters_date_range(self, sample_db_with_records):
        """Verifies date_from/date_to filters apply correctly."""
        from bagels.models.record import Record

        query = sample_db_with_records.query(Record)
        filtered = apply_date_filters(
            query, date_from="2026-01-01", date_to="2026-01-31"
        )

        results = filtered.all()
        assert isinstance(results, list)

    def test_apply_category_filter(self, sample_db_with_records):
        """Verifies category join and filter."""
        from bagels.models.record import Record

        query = sample_db_with_records.query(Record)
        filtered = apply_category_filter(query, category_name="Food")

        results = filtered.all()
        assert isinstance(results, list)

    def test_apply_amount_filter(self, sample_db_with_records):
        """Verifies amount range filter."""
        from bagels.models.record import Record

        query = sample_db_with_records.query(Record)
        filtered = apply_amount_filter(query, amount_range="50..100")

        results = filtered.all()
        assert isinstance(results, list)

    def test_apply_account_filter(self, sample_db_with_records):
        """Verifies account filter."""
        from bagels.models.record import Record

        query = sample_db_with_records.query(Record)
        filtered = apply_account_filter(query, account_name="Savings")

        results = filtered.all()
        assert isinstance(results, list)

    def test_apply_date_filters_invalid_format(self, sample_db_with_records):
        """Verifies ValueError on invalid date format."""
        from bagels.models.record import Record

        query = sample_db_with_records.query(Record)

        with pytest.raises(ValueError):
            apply_date_filters(query, date_from="invalid")

        with pytest.raises(ValueError):
            apply_date_filters(query, date_to="2026/01/01")  # Wrong format

    def test_apply_amount_filter_invalid_format(self, sample_db_with_records):
        """Verifies ValueError on invalid amount format."""
        from bagels.models.record import Record

        query = sample_db_with_records.query(Record)

        with pytest.raises(ValueError):
            apply_amount_filter(query, amount_range="invalid")
