"""
Spending command group for CLI query commands.

Provides spending analysis by category and day with multiple output formats.
"""

import click

from rich.table import Table
from rich.console import Console
from sqlalchemy import create_engine, text

from bagels.locations import database_file
from bagels.models.database.app import Session as AppSession, init_db
from bagels.models.database.db import Base
from bagels.queries.spending import (
    calculate_spending_by_category,
    calculate_spending_by_day,
)
from bagels.queries.formatters import to_json, to_yaml

console = Console()
Session = AppSession


def _open_session():
    """Open session with current DB path while allowing tests to patch Session."""
    engine = None
    if hasattr(Session, "configure"):
        engine = create_engine(f"sqlite:///{database_file().resolve()}")
        Base.metadata.create_all(engine)
        Session.configure(bind=engine)
    session = Session()
    try:
        has_account = session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='account'")
        ).scalar()
        if not has_account:
            Base.metadata.create_all(bind=session.get_bind())
    except Exception:
        Base.metadata.create_all(bind=session.get_bind())
    return session, engine


@click.group()
def spending():
    """Analyze spending patterns."""
    pass


@spending.command("by-category")
@click.option("--month", "-m", help="Month for analysis (YYYY-MM)")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
def spending_by_category(month, format):
    """Show spending breakdown by category."""
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        # Calculate spending by category
        spending_data = calculate_spending_by_category(session, month)

        if not spending_data:
            click.echo(f"No spending data for {month if month else 'current month'}.")
            return

        # Calculate total
        total_amount = sum(item["amount"] for item in spending_data)

        if format == "json":
            output = {
                "month": month or "current",
                "total": total_amount,
                "categories": spending_data,
            }
            click.echo(to_json(output))

        elif format == "yaml":
            output = {
                "month": month or "current",
                "total": total_amount,
                "categories": spending_data,
            }
            click.echo(to_yaml(output))

        else:  # table format
            table = Table(
                title=f"Spending by Category{' - ' + month if month else ''}",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Category", style="cyan", width=30)
            table.add_column("Amount", justify="right", style="yellow", width=15)
            table.add_column("Percentage", justify="right", style="white", width=12)

            for item in spending_data:
                table.add_row(
                    item["category"],
                    f"${item['amount']:.2f}",
                    f"{item['percentage']:.1f}%",
                )

            # Add total row
            table.add_row(
                "TOTAL",
                f"${total_amount:.2f}",
                "100.0%",
                style="bold yellow",
            )

            console.print(table)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@spending.command("by-day")
@click.option("--month", "-m", help="Month for analysis (YYYY-MM)")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
def spending_by_day(month, format):
    """Show daily spending breakdown."""
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        # Calculate spending by day
        spending_data = calculate_spending_by_day(session, month)

        if not spending_data:
            click.echo(f"No spending data for {month if month else 'current month'}.")
            return

        # Calculate total and average
        total_amount = sum(item["amount"] for item in spending_data)
        days_with_spending = sum(1 for item in spending_data if item["amount"] > 0)
        daily_avg = total_amount / days_with_spending if days_with_spending > 0 else 0.0

        if format == "json":
            output = {
                "month": month or "current",
                "total": total_amount,
                "daily_average": daily_avg,
                "days": spending_data,
            }
            click.echo(to_json(output))

        elif format == "yaml":
            output = {
                "month": month or "current",
                "total": total_amount,
                "daily_average": daily_avg,
                "days": spending_data,
            }
            click.echo(to_yaml(output))

        else:  # table format
            table = Table(
                title=f"Daily Spending{' - ' + month if month else ''}",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Date", style="green", width=12)
            table.add_column("Amount", justify="right", style="yellow", width=15)

            for item in spending_data:
                table.add_row(
                    item["date"],
                    f"${item['amount']:.2f}",
                )

            # Add summary row
            table.add_row(
                "AVERAGE",
                f"${daily_avg:.2f}",
                style="bold yellow",
            )

            console.print(table)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()
