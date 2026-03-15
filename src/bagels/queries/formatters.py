"""
Output formatter module for CLI query commands.

Provides table/JSON/YAML rendering functions with consistent styling
and datetime serialization.
"""

import json
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None

from rich.table import Table
from rich.console import Console

from bagels.models.record import Record
from bagels.models.account import Account
from bagels.models.category import Category


console = Console()


def format_records(records: list[Record], output_format: str = "table") -> str:
    """Format records list as table, JSON, or YAML."""
    if not records:
        return "No records found."

    if output_format == "json":
        return to_json([_record_to_dict(r) for r in records])
    elif output_format == "yaml":
        return to_yaml([_record_to_dict(r) for r in records])
    else:  # table
        table = Table(title="Records", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=20)
        table.add_column("Date", style="green", width=12)
        table.add_column("Label", style="white", width=30)
        table.add_column("Amount", justify="right", style="yellow", width=12)
        table.add_column("Category", style="magenta", width=20)
        table.add_column("Account", style="blue", width=15)

        for record in records:
            # Use slug if available, otherwise fall back to ID
            record_id = record.slug if record.slug else str(record.id)
            date_str = record.date.strftime("%Y-%m-%d") if record.date else "N/A"
            amount_str = f"${record.amount:.2f}"

            # Handle category
            category_name = record.category.name if record.category else "None"

            # Handle account
            account_name = record.account.name if record.account else "None"

            table.add_row(
                record_id,
                date_str,
                record.label,
                amount_str,
                category_name,
                account_name,
            )

        # Capture table output as string
        with console.capture() as capture:
            console.print(table)
        return capture.get()


def format_accounts(accounts: list[Account], output_format: str = "table") -> str:
    """Format accounts list as table, JSON, or YAML."""
    if not accounts:
        return "No accounts found."

    if output_format == "json":
        return to_json([_account_to_dict(a) for a in accounts])
    elif output_format == "yaml":
        return to_yaml([_account_to_dict(a) for a in accounts])
    else:  # table
        table = Table(title="Accounts", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Name", style="white", width=25)
        table.add_column("Balance", justify="right", style="yellow", width=15)

        for account in accounts:
            account_id = str(account.id)
            balance_str = f"${account.beginningBalance:.2f}"
            table.add_row(account_id, account.name, balance_str)

        with console.capture() as capture:
            console.print(table)
        return capture.get()


def format_categories(categories: list[Category], output_format: str = "table") -> str:
    """Format categories list as table, JSON, or YAML."""
    if not categories:
        return "No categories found."

    if output_format == "json":
        return to_json([_category_to_dict(c) for c in categories])
    elif output_format == "yaml":
        return to_yaml([_category_to_dict(c) for c in categories])
    else:  # table
        table = Table(title="Categories", show_header=True, header_style="bold magenta")
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Name", style="white", width=25)
        table.add_column("Nature", style="green", width=12)
        table.add_column("Parent", style="blue", width=20)

        for category in categories:
            category_id = str(category.id)
            parent_name = category.parent.name if category.parent else "None"
            table.add_row(
                category_id, category.name, category.nature or "None", parent_name
            )

        with console.capture() as capture:
            console.print(table)
        return capture.get()


def format_summary(summary: dict, output_format: str = "table") -> str:
    """Format summary data as table, JSON, or YAML."""
    if not summary:
        return "No summary data available."

    if output_format == "json":
        return to_json(summary)
    elif output_format == "yaml":
        return to_yaml(summary)
    else:  # table
        table = Table(title="Summary", show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="white", width=30)
        table.add_column("Value", justify="right", style="yellow", width=20)

        for key, value in summary.items():
            # Format value
            if isinstance(value, float):
                value_str = f"${value:.2f}"
            elif isinstance(value, int):
                value_str = str(value)
            else:
                value_str = str(value)

            table.add_row(key, value_str)

        with console.capture() as capture:
            console.print(table)
        return capture.get()


def to_json(data: list | dict) -> str:
    """
    Convert data to JSON string with datetime serialization.

    Args:
        data: List or dict to serialize

    Returns:
        JSON string with 2-space indentation
    """
    return json.dumps(data, default=str, indent=2)


def to_yaml(data: list | dict) -> str:
    """
    Convert data to YAML string with datetime serialization.

    Args:
        data: List or dict to serialize

    Returns:
        YAML string in readable format
    """
    if yaml is None:
        raise ImportError("PyYAML is not installed. Run: pip install pyyaml")

    return yaml.dump(data, default_flow_style=False, allow_unicode=True)


def _record_to_dict(record: Record) -> dict[str, Any]:
    """Convert Record to dict with nested objects (category.name, account.name)."""
    return {
        "id": record.slug if record.slug else record.id,
        "label": record.label,
        "amount": record.amount,
        "date": record.date.isoformat() if record.date else None,
        "is_income": record.isIncome,
        "is_transfer": record.isTransfer,
        "category": {"id": record.category.id, "name": record.category.name}
        if record.category
        else None,
        "account": {"id": record.account.id, "name": record.account.name}
        if record.account
        else None,
        "transfer_to_account": {
            "id": record.transferToAccount.id,
            "name": record.transferToAccount.name,
        }
        if record.transferToAccount
        else None,
        "created_at": record.createdAt.isoformat() if record.createdAt else None,
        "updated_at": record.updatedAt.isoformat() if record.updatedAt else None,
    }


def _account_to_dict(account: Account) -> dict[str, Any]:
    """Convert Account to dict."""
    return {
        "id": account.id,
        "name": account.name,
        "beginning_balance": account.beginningBalance,
        "description": account.description,
        "hidden": account.hidden,
    }


def _category_to_dict(category: Category) -> dict[str, Any]:
    """Convert Category to dict with parent.name."""
    result = {
        "id": category.id,
        "name": category.name,
        "nature": category.nature,
        "color": category.color,
    }
    if category.parent:
        result["parent"] = {"id": category.parent.id, "name": category.parent.name}
    return result
