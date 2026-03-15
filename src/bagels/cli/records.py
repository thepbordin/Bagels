"""
Records query commands for Bagels CLI.

Provides list and show commands for querying financial records with
comprehensive filtering capabilities.
"""

import click
from sqlalchemy.orm import joinedload

from bagels.models.database.app import get_session
from bagels.models.record import Record
from bagels.queries.formatters import format_records
from bagels.queries.filters import (
    apply_date_filters,
    apply_category_filter,
    apply_amount_filter,
    apply_account_filter,
    apply_person_filter,
)


@click.group()
def records():
    """Query and manage records."""
    pass


@records.command("list")
@click.option("--category", "-c", help="Filter by category name")
@click.option("--month", "-m", help="Filter by month (YYYY-MM)")
@click.option("--date-from", help="Start date (YYYY-MM-DD)")
@click.option("--date-to", help="End date (YYYY-MM-DD)")
@click.option("--amount", help="Amount range (e.g., 100..500)")
@click.option("--account", "-a", help="Filter by account name")
@click.option("--person", "-p", help="Filter by person name")
@click.option(
    "--format", "-f", type=click.Choice(["table", "json", "yaml"]), default="table"
)
@click.option("--limit", type=int, default=50, help="Maximum records to display")
@click.option("--all", is_flag=True, help="Show all records (no limit)")
def list_records(
    category,
    month,
    date_from,
    date_to,
    amount,
    account,
    person,
    format,
    limit,
    all,
):
    """List records with optional filters."""
    session = next(get_session())
    try:
        # Build query with eager loading
        query = (
            session.query(Record)
            .options(
                joinedload(Record.category),
                joinedload(Record.account),
                joinedload(Record.transferToAccount),
            )
            .filter(Record.transferToAccount.is_(None))
        )

        # Apply filters
        try:
            query = apply_date_filters(query, month, date_from, date_to)
            query = apply_category_filter(query, category)
            query = apply_amount_filter(query, amount)
            query = apply_account_filter(query, account)
            query = apply_person_filter(query, person)
        except ValueError as e:
            raise click.ClickException(str(e))

        # Apply limit (unless --all flag is set)
        if not all:
            query = query.limit(limit)
            limit_applied = limit
        else:
            limit_applied = None

        # Execute query
        records = query.order_by(Record.date.desc()).all()

        # Show warning if limit was hit
        if limit_applied and len(records) == limit_applied:
            click.echo(
                click.style(
                    f"Showing {limit_applied} most recent records. Use --all to see all records.",
                    fg="yellow",
                )
            )
            click.echo()

        # Format and display output
        output = format_records(records, format)
        click.echo(output)

    finally:
        session.close()


@records.command("show")
@click.argument("record_id", type=str)
@click.option(
    "--format", "-f", type=click.Choice(["table", "json", "yaml"]), default="table"
)
def show_record(record_id, format):
    """Show details for a single record."""
    session = next(get_session())
    try:
        # Try to parse as integer ID first, then as slug
        try:
            record_id_int = int(record_id)
            record = (
                session.query(Record)
                .options(
                    joinedload(Record.category),
                    joinedload(Record.account),
                    joinedload(Record.transferToAccount),
                )
                .filter(Record.id == record_id_int)
                .first()
            )
        except ValueError:
            # Not an integer, try as slug
            record = (
                session.query(Record)
                .options(
                    joinedload(Record.category),
                    joinedload(Record.account),
                    joinedload(Record.transferToAccount),
                )
                .filter(Record.slug == record_id)
                .first()
            )

        if not record:
            raise click.ClickException(f"Record '{record_id}' not found")

        # Format and display output
        output = format_records([record], format)
        click.echo(output)

    finally:
        session.close()
