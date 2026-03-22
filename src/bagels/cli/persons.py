"""
Persons CLI command group for Bagels.

Provides the 'bagels persons' command group with subcommands for
querying and managing persons.
"""

import click
from sqlalchemy import create_engine, text

from bagels.locations import database_file
from bagels.models.database.app import Session as AppSession, init_db
from bagels.models.database.db import Base
from bagels.queries.formatters import format_persons

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
        has_person = session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='person'")
        ).scalar()
        if not has_person:
            Base.metadata.create_all(bind=session.get_bind())
    except Exception:
        Base.metadata.create_all(bind=session.get_bind())
    return session, engine


@click.group()
def persons():
    """Query and manage persons."""
    pass


@persons.command("list")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def list_persons(format: str):
    """List all persons."""
    from bagels.models.person import Person
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        persons_list = session.query(Person).filter(Person.deletedAt.is_(None)).all()

        if not persons_list:
            click.echo("No persons found.")
            return

        output = format_persons(persons_list, output_format=format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@persons.command("add")
@click.option("--name", default=None, help="Person name")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def add_person(name, format: str):
    """Create a new person."""
    from bagels.managers.persons import create_person
    from bagels.config import load_config

    load_config()
    init_db()

    if name is None:
        name = click.prompt("Person name")

    session, engine = _open_session()
    try:
        new_person = create_person({"name": name})
        output = format_persons([new_person], output_format=format)
        click.echo(output)
    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@persons.command("show")
@click.argument("identifier", type=str)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def show_person(identifier: str, format: str):
    """Show details for a single person."""
    from bagels.models.person import Person
    from bagels.cli._helpers import resolve_entity
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        person = resolve_entity(session, Person, identifier)
        if person is None:
            raise click.ClickException(f"Person '{identifier}' not found")

        output = format_persons([person], output_format=format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@persons.command("update")
@click.argument("identifier", type=str)
@click.option("--name", default=None, help="New person name")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def update_person(identifier: str, name, format: str):
    """Update an existing person."""
    from bagels.models.person import Person
    from bagels.managers.persons import update_person as _update_person
    from bagels.cli._helpers import resolve_entity
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        person = resolve_entity(session, Person, identifier)
        if person is None:
            raise click.ClickException(f"Person '{identifier}' not found")

        if name is None:
            raise click.ClickException("No fields to update. Use --name.")

        updated = _update_person(person.id, {"name": name})
        output = format_persons([updated], output_format=format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@persons.command("delete")
@click.argument("identifier", type=str)
@click.option("--force", is_flag=True, default=False, help="Skip confirmation prompt")
@click.option(
    "--cascade",
    is_flag=True,
    default=False,
    help="Soft-delete linked records instead of blocking",
)
def delete_person(identifier: str, force: bool, cascade: bool):
    """Delete a person."""
    from bagels.models.person import Person
    from bagels.managers.persons import delete_person as _delete_person
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
        person = resolve_entity(session, Person, identifier)
        if person is None:
            raise click.ClickException(f"Person '{identifier}' not found")

        count = check_cascade_records(session, "Person", person.id)
        if count > 0 and not cascade:
            raise click.ClickException(
                f"Person '{person.name}' has {count} linked split(s). "
                "Use --cascade to delete person and soft-delete all linked records."
            )

        if not confirm_delete("person", person.name, force):
            click.echo("Cancelled.", err=True)
            return

        # Soft-delete records linked via splits if cascade is requested
        if cascade and count > 0:
            from bagels.models.split import Split
            from bagels.models.record import Record
            from datetime import datetime

            splits = session.query(Split).filter(Split.personId == person.id).all()
            record_ids = {split.recordId for split in splits}
            for record_id in record_ids:
                record = session.get(Record, record_id)
                if record and record.deletedAt is None:
                    record.deletedAt = datetime.now()
            session.commit()

        _delete_person(person.id)
        click.echo(f"Deleted person '{person.name}' (ID: {person.id})")
        if cascade and count > 0:
            click.echo(f"Soft-deleted {count} linked split(s).")

    finally:
        session.close()
        if engine is not None:
            engine.dispose()
