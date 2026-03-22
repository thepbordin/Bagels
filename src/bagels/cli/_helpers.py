"""
Shared CLI helper utilities for Bagels entity commands.

Provides common patterns used across all entity CRUD commands:
ID/slug resolution, delete confirmation, cascade record counting,
and entity echo.
"""

import click


def resolve_entity(session, model_class, identifier: str):
    """Resolve an entity by integer ID or slug string.

    Args:
        session: SQLAlchemy session to use for queries.
        model_class: The SQLAlchemy model class (Account, Person, etc.).
        identifier: String from CLI — an integer ID or slug.

    Returns:
        The entity object, or None if not found.
    """
    try:
        int_val = int(identifier)
        return session.query(model_class).filter(model_class.id == int_val).first()
    except ValueError:
        return session.query(model_class).filter(model_class.slug == identifier).first()


def confirm_delete(entity_name: str, entity_display: str, force: bool) -> bool:
    """Prompt the user for delete confirmation unless --force is used.

    Args:
        entity_name: Human-readable entity type (e.g. "account", "person").
        entity_display: The display label for the specific entity (e.g. its name).
        force: If True, skip the prompt and return True immediately.

    Returns:
        True if deletion should proceed, False if the user declined.
    """
    if force:
        return True
    return click.confirm(f"Delete {entity_name} '{entity_display}'? ", default=False)


def check_cascade_records(session, model_class_name: str, entity_id: int) -> int:
    """Count records linked to the given entity.

    For "Account": counts Record rows where accountId == entity_id.
    For "Category": counts Record rows where categoryId == entity_id.
    For "Person": counts Split rows where personId == entity_id (each split
                  is tied to a record via recordId).

    Args:
        session: SQLAlchemy session.
        model_class_name: Name string ("Account", "Category", or "Person").
        entity_id: Primary key of the entity.

    Returns:
        Integer count of linked records/splits.
    """
    from bagels.models.record import Record
    from bagels.models.split import Split

    if model_class_name == "Account":
        return session.query(Record).filter(Record.accountId == entity_id).count()
    elif model_class_name == "Category":
        return session.query(Record).filter(Record.categoryId == entity_id).count()
    elif model_class_name == "Person":
        return session.query(Split).filter(Split.personId == entity_id).count()
    return 0


def echo_entity(entity_obj, format_fn, output_format: str) -> None:
    """Format a single entity and echo it to stdout.

    Args:
        entity_obj: The entity object to display.
        format_fn: Formatter function (e.g. format_accounts) that accepts
                   a list and output_format keyword argument.
        output_format: One of "table", "json", or "yaml".
    """
    output = format_fn([entity_obj], output_format=output_format)
    click.echo(output)
