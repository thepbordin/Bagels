"""
Accounts CLI command group for Bagels.

Provides the 'bagels accounts' command group with subcommands for
querying and managing accounts.
"""

import click
from sqlalchemy import create_engine, text

from bagels.locations import database_file
from bagels.models.database.app import Session as AppSession, init_db
from bagels.models.database.db import Base
from bagels.queries.formatters import format_accounts

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
def accounts():
    """Query and manage accounts."""
    pass


@accounts.command("list")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def list_accounts(format: str):
    """List all accounts with balances."""
    from bagels.models.account import Account
    from bagels.managers.accounts import get_account_balance
    from bagels.config import load_config

    # Load config
    load_config()

    # Initialize database
    init_db()

    # Create session bound to the current custom-root database path.
    session, engine = _open_session()
    try:
        # Query visible accounts from the active session.
        accounts_list = (
            session.query(Account)
            .filter(Account.deletedAt.is_(None), Account.hidden.is_(False))
            .all()
        )

        if not accounts_list:
            click.echo("No accounts found.")
            return

        # Calculate balances for each account
        for account in accounts_list:
            account.balance = get_account_balance(account.id, session)

        # Format and display output
        output = format_accounts(accounts_list, output_format=format)
        click.echo(output)

    except Exception as e:
        click.echo(click.style(f"Error listing accounts: {e}", fg="red"), err=True)
        raise click.ClickException(str(e))
    finally:
        session.close()
        if engine is not None:
            engine.dispose()
