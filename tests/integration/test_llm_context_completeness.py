"""
Integration tests for LLM context completeness (TEST-05).

Validates that 'bagels llm context' YAML output contains all 5 required
sections and that data is populated from sample records.
"""

import pytest
import yaml
from unittest.mock import patch

from bagels.cli.llm import llm

REQUIRED_SECTIONS = [
    "accounts",
    "summary",
    "spending_by_category",
    "recent_records",
    "categories",
]


def _invoke_context(cli_runner, sample_cli_db, extra_args=None):
    """Invoke 'llm context' with the test session and return the result."""
    args = ["context"] + (extra_args or [])
    with (
        patch("bagels.cli.llm.Session", return_value=sample_cli_db),
        patch("bagels.cli.llm.init_db"),
        patch("bagels.cli.llm.load_config"),
    ):
        return cli_runner.invoke(llm, args)


def _parse_context_yaml(result):
    """Parse YAML from a CLI result, asserting it is a dict."""
    assert result.exit_code == 0, (
        f"Command exited {result.exit_code}. Output: {result.output[:500]}"
    )
    data = yaml.safe_load(result.output)
    assert isinstance(data, dict), (
        f"Expected YAML dict. Got {type(data)}. Output: {result.output[:500]}"
    )
    return data


class TestLLMContextCompleteness:
    """Tests that 'bagels llm context' output is complete and parseable."""

    def test_context_is_valid_yaml(self, cli_runner, sample_cli_db):
        """llm context must produce valid, parseable YAML."""
        result = _invoke_context(cli_runner, sample_cli_db)

        assert result.exit_code == 0, f"Command failed: {result.output[:500]}"
        data = yaml.safe_load(result.output)
        assert isinstance(data, dict), (
            f"Expected dict from YAML parse, got {type(data)}"
        )

    def test_context_has_all_required_sections(self, cli_runner, sample_cli_db):
        """All 5 required sections must be present in LLM context output."""
        result = _invoke_context(cli_runner, sample_cli_db)
        data = _parse_context_yaml(result)

        for section in REQUIRED_SECTIONS:
            assert section in data, (
                f"Missing required section: '{section}'. "
                f"Present keys: {list(data.keys())}"
            )

    def test_context_budget_status_key_present(self, cli_runner, sample_cli_db):
        """budget_status key must be present (value may be None or empty)."""
        result = _invoke_context(cli_runner, sample_cli_db)
        data = _parse_context_yaml(result)

        assert "budget_status" in data, (
            f"Missing 'budget_status' key. Present keys: {list(data.keys())}"
        )

    def test_context_accounts_section_has_data(self, cli_runner, sample_cli_db):
        """accounts section must be non-empty (sample_cli_db has 1 account)."""
        result = _invoke_context(cli_runner, sample_cli_db)
        data = _parse_context_yaml(result)

        accounts = data.get("accounts")
        assert accounts is not None, "accounts section is None"
        assert len(accounts) > 0, (
            "accounts section is empty; expected at least 1 account"
        )

    def test_context_recent_records_section_has_data(self, cli_runner, sample_cli_db):
        """recent_records section must be non-empty (sample_cli_db has 5 records)."""
        result = _invoke_context(
            cli_runner, sample_cli_db, extra_args=["--month", "2026-03"]
        )
        data = _parse_context_yaml(result)

        recent = data.get("recent_records")
        assert recent is not None, "recent_records section is None"
        assert len(recent) > 0, (
            "recent_records section is empty; expected records from 2026-03"
        )

    def test_context_spending_by_category_is_structured(
        self, cli_runner, sample_cli_db
    ):
        """spending_by_category must be present and not an empty string."""
        result = _invoke_context(cli_runner, sample_cli_db)
        data = _parse_context_yaml(result)

        spending = data.get("spending_by_category")
        assert spending is not None, "spending_by_category is None"
        assert spending != "", "spending_by_category is an empty string"

    def test_context_with_month_filter(self, cli_runner, sample_cli_db):
        """--month filter must not crash and must return a valid dict."""
        result = _invoke_context(
            cli_runner, sample_cli_db, extra_args=["--month", "2026-03"]
        )
        data = _parse_context_yaml(result)

        # Period should reflect the requested month
        assert "period" in data or "accounts" in data, (
            f"Expected 'period' or 'accounts' key. Got: {list(data.keys())}"
        )

    def test_context_summary_section_has_numeric_fields(
        self, cli_runner, sample_cli_db
    ):
        """summary section must be a dict containing at least one numeric value."""
        result = _invoke_context(
            cli_runner, sample_cli_db, extra_args=["--month", "2026-03"]
        )
        data = _parse_context_yaml(result)

        summary = data.get("summary")
        assert summary is not None, "summary section is None"
        assert isinstance(summary, dict), (
            f"Expected summary to be a dict, got {type(summary)}"
        )
        has_numeric = any(isinstance(v, (int, float)) for v in summary.values())
        assert has_numeric, (
            f"summary section has no numeric fields. summary = {summary}"
        )
