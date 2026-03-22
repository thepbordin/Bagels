"""
Templates CLI command group for Bagels.

Provides the 'bagels templates' command group with subcommands for
querying and managing record templates.
"""

import click
from sqlalchemy import create_engine, text

from bagels.locations import database_file
from bagels.models.database.app import Session as AppSession, init_db
from bagels.models.database.db import Base
from bagels.queries.formatters import format_templates

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
def templates():
    """Query and manage record templates."""
    pass


@templates.command("list")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def list_templates(format: str):
    """List all record templates."""
    from bagels.managers.record_templates import get_all_templates
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        templates_list = get_all_templates()

        if not templates_list:
            click.echo("No templates found.")
            return

        output = format_templates(templates_list, output_format=format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@templates.command("show")
@click.argument("identifier", type=str)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def show_template(identifier: str, format: str):
    """Show details for a single record template."""
    from bagels.models.record_template import RecordTemplate
    from bagels.cli._helpers import resolve_entity
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        template = resolve_entity(session, RecordTemplate, identifier)
        if template is None:
            raise click.ClickException(f"Template '{identifier}' not found")

        output = format_templates([template], output_format=format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@templates.command("add")
@click.option("--label", default=None, help="Template label")
@click.option("--amount", default=None, type=float, help="Template amount")
@click.option("--account-id", default=None, type=int, help="Account ID")
@click.option("--category-id", default=None, type=int, help="Category ID (optional)")
@click.option("--income", is_flag=True, default=False, help="Mark as income")
@click.option("--transfer", is_flag=True, default=False, help="Mark as transfer")
@click.option(
    "--transfer-to-account-id",
    default=None,
    type=int,
    help="Transfer target account ID",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def add_template(
    label,
    amount,
    account_id,
    category_id,
    income,
    transfer,
    transfer_to_account_id,
    format: str,
):
    """Create a new record template."""
    from bagels.models.account import Account
    from bagels.models.category import Category
    from bagels.managers.record_templates import create_template
    from bagels.config import load_config

    load_config()
    init_db()

    if label is None:
        label = click.prompt("Template label")
    if amount is None:
        amount = click.prompt("Amount", type=float)
    if account_id is None:
        account_id = click.prompt("Account ID", type=int)

    if transfer and transfer_to_account_id is None:
        transfer_to_account_id = click.prompt("Transfer to Account ID", type=int)

    session, engine = _open_session()
    try:
        account = session.query(Account).filter(Account.id == account_id).first()
        if account is None:
            raise click.ClickException(f"Account ID {account_id} not found")

        if category_id is not None:
            category = (
                session.query(Category)
                .filter(Category.id == category_id, Category.deletedAt.is_(None))
                .first()
            )
            if category is None:
                raise click.ClickException(f"Category ID {category_id} not found")

        if transfer_to_account_id is not None:
            transfer_account = (
                session.query(Account)
                .filter(Account.id == transfer_to_account_id)
                .first()
            )
            if transfer_account is None:
                raise click.ClickException(
                    f"Transfer target account ID {transfer_to_account_id} not found"
                )

        data = {
            "label": label,
            "amount": amount,
            "accountId": account_id,
            "isIncome": income,
            "isTransfer": transfer,
        }
        if category_id is not None:
            data["categoryId"] = category_id
        if transfer_to_account_id is not None:
            data["transferToAccountId"] = transfer_to_account_id

        new_template = create_template(data)
        output = format_templates([new_template], output_format=format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@templates.command("update")
@click.argument("identifier", type=str)
@click.option("--label", default=None, help="New template label")
@click.option("--amount", default=None, type=float, help="New template amount")
@click.option("--account-id", default=None, type=int, help="New account ID")
@click.option("--category-id", default=None, type=int, help="New category ID")
@click.option("--income/--no-income", default=None, help="Set income flag")
@click.option("--transfer/--no-transfer", default=None, help="Set transfer flag")
@click.option(
    "--transfer-to-account-id",
    default=None,
    type=int,
    help="New transfer target account ID",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def update_template_cmd(
    identifier: str,
    label,
    amount,
    account_id,
    category_id,
    income,
    transfer,
    transfer_to_account_id,
    format: str,
):
    """Update an existing record template."""
    from bagels.models.record_template import RecordTemplate
    from bagels.models.account import Account
    from bagels.models.category import Category
    from bagels.managers.record_templates import update_template
    from bagels.cli._helpers import resolve_entity
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        template = resolve_entity(session, RecordTemplate, identifier)
        if template is None:
            raise click.ClickException(f"Template '{identifier}' not found")

        update_data = {}
        if label is not None:
            update_data["label"] = label
        if amount is not None:
            update_data["amount"] = amount
        if account_id is not None:
            update_data["accountId"] = account_id
        if category_id is not None:
            update_data["categoryId"] = category_id
        if income is not None:
            update_data["isIncome"] = income
        if transfer is not None:
            update_data["isTransfer"] = transfer
        if transfer_to_account_id is not None:
            update_data["transferToAccountId"] = transfer_to_account_id

        if not update_data:
            raise click.ClickException(
                "No fields to update. Use --label, --amount, --account-id, "
                "--category-id, --income/--no-income, --transfer/--no-transfer, "
                "or --transfer-to-account-id."
            )

        if account_id is not None:
            account = session.query(Account).filter(Account.id == account_id).first()
            if account is None:
                raise click.ClickException(f"Account ID {account_id} not found")

        if category_id is not None:
            category = (
                session.query(Category)
                .filter(Category.id == category_id, Category.deletedAt.is_(None))
                .first()
            )
            if category is None:
                raise click.ClickException(f"Category ID {category_id} not found")

        updated = update_template(template.id, update_data)
        output = format_templates([updated], output_format=format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@templates.command("delete")
@click.argument("identifier", type=str)
@click.option("--force", is_flag=True, default=False, help="Skip confirmation prompt")
def delete_template_cmd(identifier: str, force: bool):
    """Delete a record template."""
    from bagels.models.record_template import RecordTemplate
    from bagels.managers.record_templates import delete_template
    from bagels.cli._helpers import resolve_entity, confirm_delete
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        template = resolve_entity(session, RecordTemplate, identifier)
        if template is None:
            raise click.ClickException(f"Template '{identifier}' not found")

        if not confirm_delete("template", template.label, force):
            click.echo("Cancelled.", err=True)
            return

        delete_template(template.id)
        click.echo(f"Deleted template '{template.label}' (ID: {template.id})")

    finally:
        session.close()
        if engine is not None:
            engine.dispose()
