"""
Summary CLI command for Bagels.

Provides the 'bagels summary' command to display financial overview
including income, expenses, and net savings for a specified month.
"""

import click
from datetime import datetime
from sqlalchemy import create_engine

from bagels.locations import database_file
from bagels.models.database.app import Session as AppSession, init_db
from bagels.queries.summaries import calculate_monthly_summary
from bagels.queries.formatters import format_summary

Session = AppSession


def _open_session():
    """Open session with current DB path while allowing tests to patch Session."""
    engine = None
    if hasattr(Session, "configure"):
        engine = create_engine(f"sqlite:///{database_file().resolve()}")
        Session.configure(bind=engine)
    session = Session()
    return session, engine


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

    # Create session bound to the active database path.
    session, engine = _open_session()
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
        if engine is not None:
            engine.dispose()
