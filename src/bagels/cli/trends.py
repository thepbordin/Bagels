"""
Trends comparison command for CLI.

Provides month-over-month spending comparison and category trend analysis.
"""

import click
from rich.table import Table
from rich.console import Console

from bagels.models.database.app import init_db, Session
from bagels.config import load_config
from bagels.queries.trends import (
    calculate_monthly_comparison,
    calculate_category_trends,
)
from bagels.queries.formatters import to_json, to_yaml

console = Console()


@click.command()
@click.option(
    "--months", "-m", type=int, default=3, help="Number of months to compare (1-12)"
)
@click.option("--category", "-c", help="Filter by category name")
@click.option(
    "--format", "-f", type=click.Choice(["table", "json", "yaml"]), default="table"
)
def trends(months, category, format):
    """Compare spending across multiple months.

    Displays month-over-month comparison of income, expenses, and savings
    with percentage change indicators.
    """
    # Load config
    load_config()

    # Initialize database
    init_db()

    # Validate months parameter
    if months < 1 or months > 12:
        click.echo("Error: months must be between 1 and 12")
        return

    session = Session()

    try:
        if category:
            # Category-specific trends
            category_data = calculate_category_trends(session, months)

            if category not in category_data:
                click.echo(
                    f"Error: Category '{category}' not found or has no spending data"
                )
                return

            if format == "json":
                click.echo(to_json(category_data[category]))
            elif format == "yaml":
                click.echo(to_yaml(category_data[category]))
            else:
                _display_category_trends_table(category, category_data[category])
        else:
            # Monthly comparison
            monthly_data = calculate_monthly_comparison(session, months)

            if format == "json":
                click.echo(to_json(monthly_data))
            elif format == "yaml":
                click.echo(to_yaml(monthly_data))
            else:
                _display_monthly_comparison_table(monthly_data)

    finally:
        session.close()


def _display_monthly_comparison_table(monthly_data):
    """Display monthly comparison as a formatted table."""
    table = Table(
        title="Monthly Spending Comparison",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Month", style="cyan", width=12)
    table.add_column("Income", justify="right", style="green", width=15)
    table.add_column("Expenses", justify="right", style="red", width=15)
    table.add_column("Savings", justify="right", style="yellow", width=15)
    table.add_column("Change", justify="right", style="white", width=12)

    for month_data in monthly_data:
        # Format currency values
        income_str = f"${month_data['total_income']:.2f}"
        expenses_str = f"${month_data['total_expenses']:.2f}"
        savings_str = f"${month_data['net_savings']:.2f}"

        # Format change percentage
        if month_data["change_percentage"] is not None:
            change_pct = month_data["change_percentage"]
            change_dir = month_data["change_direction"]

            if change_dir == "up":
                arrow = "↑"
                color = "green"
            elif change_dir == "down":
                arrow = "↓"
                color = "red"
            else:
                arrow = "→"
                color = "white"

            change_str = f"{arrow} {abs(change_pct):.1f}%"
        else:
            change_str = "N/A"
            color = "white"

        table.add_row(
            month_data["month"],
            income_str,
            expenses_str,
            savings_str,
            change_str,
            style=color if month_data["change_percentage"] is not None else None,
        )

    console.print(table)


def _display_category_trends_table(category_name, category_data):
    """Display category trends as a formatted table."""
    table = Table(
        title=f"Category Trends: {category_name}",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Month", style="cyan", width=12)
    table.add_column("Amount", justify="right", style="yellow", width=15)

    for month_data in category_data:
        amount_str = f"${month_data['amount']:.2f}"
        table.add_row(month_data["month"], amount_str)

    console.print(table)
