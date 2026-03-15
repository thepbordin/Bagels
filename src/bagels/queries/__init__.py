"""
Bagels query layer.

Provides shared utilities for CLI query commands including output formatters
and filter functions.
"""

from bagels.queries.formatters import (
    format_records,
    format_accounts,
    format_categories,
    format_summary,
    to_json,
    to_yaml,
)

from bagels.queries.filters import (
    parse_month,
    parse_amount_range,
    apply_date_filters,
    apply_category_filter,
    apply_amount_filter,
)

__all__ = [
    "format_records",
    "format_accounts",
    "format_categories",
    "format_summary",
    "to_json",
    "to_yaml",
    "parse_month",
    "parse_amount_range",
    "apply_date_filters",
    "apply_category_filter",
    "apply_amount_filter",
]
