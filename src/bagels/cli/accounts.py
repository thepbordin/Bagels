"""
Accounts CLI command group for Bagels.

Provides the 'bagels accounts' command group with subcommands for
querying and managing accounts.
"""

from datetime import datetime

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


@accounts.command("show")
@click.argument("identifier", type=str)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def show_account(identifier: str, format: str):
    """Show details for a single account."""
    from bagels.models.account import Account
    from bagels.managers.accounts import get_account_balance
    from bagels.cli._helpers import resolve_entity
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        account = resolve_entity(session, Account, identifier)
        if account is None:
            raise click.ClickException(f"Account '{identifier}' not found")

        account.balance = get_account_balance(account.id, session)
        output = format_accounts([account], output_format=format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@accounts.command("add")
@click.option("--name", default=None, help="Account name")
@click.option("--balance", default=None, type=float, help="Beginning balance")
@click.option("--description", default=None, help="Account description")
@click.option("--hidden", is_flag=True, default=False, help="Mark account as hidden")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def add_account(name, balance, description, hidden, format: str):
    """Create a new account."""
    from bagels.managers.accounts import create_account
    from bagels.config import load_config

    load_config()
    init_db()

    if name is None:
        name = click.prompt("Account name")
    if balance is None:
        balance = click.prompt("Beginning balance", type=float)

    data = {"name": name, "beginningBalance": balance}
    if description is not None:
        data["description"] = description
    if hidden:
        data["hidden"] = hidden

    session, engine = _open_session()
    try:
        new_account = create_account(data)
        output = format_accounts([new_account], output_format=format)
        click.echo(output)
    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@accounts.command("update")
@click.argument("identifier", type=str)
@click.option("--name", default=None, help="New account name")
@click.option("--balance", default=None, type=float, help="New beginning balance")
@click.option("--description", default=None, help="New account description")
@click.option("--hidden/--no-hidden", default=None, help="Set account visibility")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def update_account(identifier: str, name, balance, description, hidden, format: str):
    """Update an existing account."""
    from bagels.models.account import Account
    from bagels.managers.accounts import update_account as _update_account
    from bagels.cli._helpers import resolve_entity
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        account = resolve_entity(session, Account, identifier)
        if account is None:
            raise click.ClickException(f"Account '{identifier}' not found")

        update_data = {}
        if name is not None:
            update_data["name"] = name
        if balance is not None:
            update_data["beginningBalance"] = balance
        if description is not None:
            update_data["description"] = description
        if hidden is not None:
            update_data["hidden"] = hidden

        if not update_data:
            raise click.ClickException(
                "No fields to update. Use --name, --balance, --description, or --hidden."
            )

        updated = _update_account(account.id, update_data)
        output = format_accounts([updated], output_format=format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@accounts.command("delete")
@click.argument("identifier", type=str)
@click.option("--force", is_flag=True, default=False, help="Skip confirmation prompt")
@click.option(
    "--cascade",
    is_flag=True,
    default=False,
    help="Soft-delete all linked records instead of blocking",
)
def delete_account(identifier: str, force: bool, cascade: bool):
    """Delete an account."""
    from bagels.models.account import Account
    from bagels.managers.accounts import delete_account as _delete_account
    from bagels.cli._helpers import (
        resolve_entity,
        confirm_delete,
        check_cascade_records,
    )
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        account = resolve_entity(session, Account, identifier)
        if account is None:
            raise click.ClickException(f"Account '{identifier}' not found")

        count = check_cascade_records(session, "Account", account.id)
        if count > 0 and not cascade:
            raise click.ClickException(
                f"Account '{account.name}' has {count} linked record(s). "
                "Use --cascade to delete account and soft-delete all linked records."
            )

        if not confirm_delete("account", account.name, force):
            click.echo("Cancelled.", err=True)
            return

        # Soft-delete linked records if cascade is requested
        if cascade and count > 0:
            from bagels.models.record import Record

            linked_records = (
                session.query(Record).filter(Record.accountId == account.id).all()
            )
            for record in linked_records:
                record.deletedAt = datetime.now()
            session.commit()

        _delete_account(account.id)
        click.echo(f"Deleted account '{account.name}' (ID: {account.id})")
        if cascade and count > 0:
            click.echo(f"Soft-deleted {count} linked record(s).")

    finally:
        session.close()
        if engine is not None:
            engine.dispose()
