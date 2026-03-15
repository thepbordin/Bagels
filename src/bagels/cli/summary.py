"""
Summary CLI command for Bagels.

Provides the 'bagels summary' command to display financial overview
including income, expenses, and net savings for a specified month.
"""

import click
from datetime import datetime

from bagels.models.database.app import init_db, Session
from bagels.queries.summaries import calculate_monthly_summary
from bagels.queries.formatters import format_summary


@click.command()
@click.option("--month", "-m", help="Month for summary (YYYY-MM), defaults to current")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def summary(month: str | None, format: str):
    """Show financial summary for a month."""
    # Load config
    from bagels.config import load_config

    load_config()

    # Initialize database
    init_db()

    # Create session
    session = Session()
    try:
        # Handle current month default
        if month is None:
            # Use current month
            now = datetime.now()
            month = now.strftime("%Y-%m")

        # Calculate summary
        summary_data = calculate_monthly_summary(session, month)

        # Format and display output
        output = format_summary(summary_data, output_format=format)
        click.echo(output)

    except ValueError as e:
        click.echo(click.style(f"Error: {e}", fg="red"), err=True)
        raise click.ClickException(str(e))
    except Exception as e:
        click.echo(click.style(f"Error calculating summary: {e}", fg="red"), err=True)
        raise click.ClickException(str(e))
    finally:
        session.close()
