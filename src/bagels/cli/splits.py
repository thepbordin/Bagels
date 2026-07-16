"""
Splits management commands for Bagels CLI.

Provides add, list, mark-paid, and delete commands for managing
expense splits on records.
"""

import click
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import joinedload

from bagels.locations import database_file
from bagels.models.database.app import Session as AppSession, init_db
from bagels.models.record import Record
from bagels.models.split import Split
from bagels.models.person import Person
from bagels.cli._helpers import resolve_entity, confirm_delete

Session = AppSession


def _open_session():
    """Open session with current DB path."""
    engine = None
    if hasattr(Session, "configure"):
        engine = create_engine(f"sqlite:///{database_file().resolve()}")
        Session.configure(bind=engine)
    session = Session()
    return session, engine


@click.group()
def splits():
    """Manage expense splits on records."""
    pass


@splits.command("add")
@click.argument("record_id", type=str)
@click.option("--person", "-p", required=True, help="Person slug or integer ID")
@click.option("--amount", "-a", type=float, required=True, help="Split amount")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
def add_split_cmd(record_id, person, amount, format):
    """Add a split to an existing record."""
    from bagels.config import load_config
    from bagels.managers.splits import create_split

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        # Resolve record
        record = resolve_entity(session, Record, record_id)
        if record is None:
            raise click.ClickException(f"Record '{record_id}' not found")

        # Resolve person by slug or ID
        person_obj = resolve_entity(session, Person, person)
        if person_obj is None:
            raise click.ClickException(f"Person '{person}' not found")

        # Validate amount
        if amount <= 0:
            raise click.ClickException("Split amount must be greater than 0")

        split_data = {
            "recordId": record.id,
            "personId": person_obj.id,
            "amount": amount,
        }
        new_split = create_split(split_data)

        # Display result
        _echo_split(new_split, session, format)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@splits.command("list")
@click.argument("record_id", type=str)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
def list_splits_cmd(record_id, format):
    """List splits for a record."""
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        record = resolve_entity(session, Record, record_id)
        if record is None:
            raise click.ClickException(f"Record '{record_id}' not found")

        split_list = (
            session.query(Split)
            .options(joinedload(Split.person))
            .filter(Split.recordId == record.id)
            .all()
        )

        if not split_list:
            click.echo(f"No splits found for record '{record_id}'.")
            return

        _echo_splits_list(split_list, format)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@splits.command("mark-paid")
@click.argument("split_id", type=int)
def mark_paid_cmd(split_id):
    """Mark a split as paid (sets isPaid=True, paidDate=today)."""
    from bagels.config import load_config
    from bagels.managers.splits import update_split, get_split_by_id

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        split = get_split_by_id(split_id)
        if split is None:
            raise click.ClickException(f"Split with ID {split_id} not found")

        update_split(
            split_id,
            {
                "isPaid": True,
                "paidDate": datetime.now(),
            },
        )

        click.echo(
            f"Split {split_id} marked as paid (date: {datetime.now().strftime('%Y-%m-%d')})"
        )

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@splits.command("delete")
@click.argument("split_id", type=int)
@click.option("--force", is_flag=True, default=False, help="Skip confirmation prompt")
def delete_split_cmd(split_id, force):
    """Delete a split."""
    from bagels.config import load_config
    from bagels.managers.splits import get_split_by_id, delete_split

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        split = get_split_by_id(split_id)
        if split is None:
            raise click.ClickException(f"Split with ID {split_id} not found")

        display_str = f"split #{split_id} (${split.amount:.2f})"
        if not confirm_delete("split", display_str, force):
            click.echo("Cancelled.", err=True)
            return

        delete_split(split_id)
        click.echo(f"Deleted split #{split_id}")

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


def _echo_split(split, session, output_format):
    """Display a single split."""
    # Reload with person relationship
    loaded = (
        session.query(Split)
        .options(joinedload(Split.person))
        .filter(Split.id == split.id)
        .first()
    )
    if loaded is None:
        click.echo(f"Split #{split.id} created.")
        return
    _echo_splits_list([loaded], output_format)


def _echo_splits_list(split_list, output_format):
    """Display a list of splits."""
    import json

    try:
        import yaml
    except ImportError:
        yaml = None

    if output_format == "json":
        data = [_split_to_dict(s) for s in split_list]
        click.echo(json.dumps(data, default=str, indent=2))
    elif output_format == "yaml":
        if yaml is None:
            raise click.ClickException("PyYAML not installed")
        data = [_split_to_dict(s) for s in split_list]
        click.echo(yaml.dump(data, default_flow_style=False, allow_unicode=True))
    else:
        from rich.table import Table
        from rich.console import Console

        table = Table(title="Splits", show_header=True, header_style="bold cyan")
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Person", style="white", width=20)
        table.add_column("Amount", justify="right", style="yellow", width=12)
        table.add_column("Paid", style="green", width=8)
        table.add_column("Paid Date", style="blue", width=12)

        for s in split_list:
            person_name = (
                s.person.name if hasattr(s, "person") and s.person else f"#{s.personId}"
            )
            paid_str = "Yes" if s.isPaid else "No"
            paid_date_str = s.paidDate.strftime("%Y-%m-%d") if s.paidDate else ""
            table.add_row(
                str(s.id), person_name, f"${s.amount:.2f}", paid_str, paid_date_str
            )

        con = Console()
        with con.capture() as capture:
            con.print(table)
        click.echo(capture.get())


def _split_to_dict(split):
    return {
        "id": split.id,
        "record_id": split.recordId,
        "person": split.person.name
        if hasattr(split, "person") and split.person
        else None,
        "person_id": split.personId,
        "amount": split.amount,
        "is_paid": split.isPaid,
        "paid_date": split.paidDate.isoformat() if split.paidDate else None,
    }
