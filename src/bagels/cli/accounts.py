"""
Accounts CLI command group for Bagels.

Provides the 'bagels accounts' command group with subcommands for
querying and managing accounts.
"""

import click

from bagels.models.database.app import init_db, Session
from bagels.queries.formatters import format_accounts


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
    from bagels.managers.accounts import get_all_accounts, get_account_balance
    from bagels.config import load_config

    # Load config
    load_config()

    # Initialize database
    init_db()

    # Create session
    session = Session()
    try:
        # Query accounts
        accounts_list = get_all_accounts(session)

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
