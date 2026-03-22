"""
Categories command group for CLI query commands.

Provides tree display of category hierarchies with multiple output formats,
plus full CRUD subcommands: tree, list, show, add, update, delete.
"""

import click

from rich.table import Table
from rich.console import Console
from rich.text import Text
from sqlalchemy import create_engine, text

from bagels.config import load_config
from bagels.locations import database_file
from bagels.models.database.app import Session as AppSession, init_db
from bagels.models.database.db import Base
from bagels.managers.categories import get_all_categories_tree
from bagels.queries.formatters import to_json, to_yaml, format_categories

console = Console()
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
def categories():
    """Query and manage categories."""
    pass


@categories.command("tree")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
def categories_tree(format):
    """Show category hierarchy as a tree."""
    load_config()
    init_db()

    session, engine = _open_session()
    try:
        # Get category tree from manager
        category_tree = get_all_categories_tree(session)

        if not category_tree:
            click.echo("No categories found.")
            return

        if format == "json":
            # Convert to flat list with parent references
            categories_data = []
            for category, node, depth in category_tree:
                cat_dict = {
                    "id": category.id,
                    "name": category.name,
                    "nature": str(category.nature),
                    "color": category.color,
                    "depth": depth,
                }
                if category.parentCategory:
                    cat_dict["parent_id"] = category.parentCategoryId
                categories_data.append(cat_dict)
            click.echo(to_json(categories_data))

        elif format == "yaml":
            # Convert to flat list with parent references
            categories_data = []
            for category, node, depth in category_tree:
                cat_dict = {
                    "id": category.id,
                    "name": category.name,
                    "nature": str(category.nature),
                    "color": category.color,
                    "depth": depth,
                }
                if category.parentCategory:
                    cat_dict["parent_id"] = category.parentCategoryId
                categories_data.append(cat_dict)
            click.echo(to_yaml(categories_data))

        else:  # table format with tree rendering
            table = Table(
                title="Category Tree", show_header=True, header_style="bold magenta"
            )
            table.add_column("Tree", style="white", width=40)
            table.add_column("Nature", style="green", width=12)
            table.add_column("Color", style="cyan", width=10)

            for category, node, depth in category_tree:
                # Build tree string with node prefix
                tree_text = Text()
                if depth == 0:
                    # Root level - just the node and name
                    tree_text.append(node)
                    tree_text.append(f" {category.name}", style=category.color)
                else:
                    # Nested level - add indentation
                    tree_text.append("  " * (depth - 1))
                    tree_text.append(node)
                    tree_text.append(f" {category.name}", style=category.color)

                # Add row
                table.add_row(
                    tree_text,
                    str(category.nature),
                    category.color,
                )

            console.print(table)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@categories.command("list")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def list_categories(format: str):
    """List all categories."""
    from bagels.models.category import Category

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        categories_list = (
            session.query(Category).filter(Category.deletedAt.is_(None)).all()
        )

        if not categories_list:
            click.echo("No categories found.")
            return

        output = format_categories(categories_list, output_format=format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@categories.command("show")
@click.argument("identifier", type=str)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def show_category(identifier: str, format: str):
    """Show details for a single category."""
    from bagels.models.category import Category
    from bagels.cli._helpers import resolve_entity

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        category = resolve_entity(session, Category, identifier)
        if category is None:
            raise click.ClickException(f"Category '{identifier}' not found")

        output = format_categories([category], output_format=format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@categories.command("add")
@click.option("--name", default=None, help="Category name")
@click.option(
    "--nature",
    default=None,
    type=click.Choice(["Want", "Need", "Must"], case_sensitive=False),
    help="Category nature",
)
@click.option("--color", default=None, help="Category color (hex, e.g. #FF5733)")
@click.option("--parent-id", default=None, type=int, help="Parent category ID")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def add_category(name, nature, color, parent_id, format: str):
    """Create a new category."""
    from bagels.models.category import Category
    from bagels.managers.categories import create_category

    load_config()
    init_db()

    if name is None:
        name = click.prompt("Category name")
    if nature is None:
        nature = click.prompt(
            "Nature (Want/Need/Must)",
            type=click.Choice(["Want", "Need", "Must"], case_sensitive=False),
        )

    data = {"name": name, "nature": nature}
    if color is not None:
        data["color"] = color
    if parent_id is not None:
        data["parentCategoryId"] = parent_id

    session, engine = _open_session()
    try:
        if parent_id is not None:
            parent = (
                session.query(Category)
                .filter(Category.id == parent_id, Category.deletedAt.is_(None))
                .first()
            )
            if parent is None:
                raise click.ClickException(f"Parent category ID {parent_id} not found")

        new_category = create_category(data)
        output = format_categories([new_category], output_format=format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@categories.command("update")
@click.argument("identifier", type=str)
@click.option("--name", default=None, help="New category name")
@click.option(
    "--nature",
    default=None,
    type=click.Choice(["Want", "Need", "Must"], case_sensitive=False),
    help="New category nature",
)
@click.option("--color", default=None, help="New category color (hex)")
@click.option("--parent-id", default=None, type=int, help="New parent category ID")
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format (default: table)",
)
def update_category_cmd(identifier: str, name, nature, color, parent_id, format: str):
    """Update an existing category."""
    from bagels.models.category import Category
    from bagels.managers.categories import update_category
    from bagels.cli._helpers import resolve_entity

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        category = resolve_entity(session, Category, identifier)
        if category is None:
            raise click.ClickException(f"Category '{identifier}' not found")

        update_data = {}
        if name is not None:
            update_data["name"] = name
        if nature is not None:
            update_data["nature"] = nature
        if color is not None:
            update_data["color"] = color
        if parent_id is not None:
            update_data["parentCategoryId"] = parent_id

        if not update_data:
            raise click.ClickException(
                "No fields to update. Use --name, --nature, --color, or --parent-id."
            )

        if parent_id is not None:
            parent = (
                session.query(Category)
                .filter(Category.id == parent_id, Category.deletedAt.is_(None))
                .first()
            )
            if parent is None:
                raise click.ClickException(f"Parent category ID {parent_id} not found")

        updated = update_category(category.id, update_data)
        output = format_categories([updated], output_format=format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@categories.command("delete")
@click.argument("identifier", type=str)
@click.option("--force", is_flag=True, default=False, help="Skip confirmation prompt")
@click.option(
    "--cascade",
    is_flag=True,
    default=False,
    help="Soft-delete all linked records instead of blocking",
)
def delete_category_cmd(identifier: str, force: bool, cascade: bool):
    """Delete a category."""
    from bagels.models.category import Category
    from bagels.managers.categories import delete_category
    from bagels.cli._helpers import (
        resolve_entity,
        confirm_delete,
        check_cascade_records,
    )

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        category = resolve_entity(session, Category, identifier)
        if category is None:
            raise click.ClickException(f"Category '{identifier}' not found")

        count = check_cascade_records(session, "Category", category.id)
        if count > 0 and not cascade:
            raise click.ClickException(
                f"Category '{category.name}' has {count} linked record(s). "
                "Use --cascade to delete category and soft-delete all linked records."
            )

        if not confirm_delete("category", category.name, force):
            click.echo("Cancelled.", err=True)
            return

        # Soft-delete linked records if cascade is requested
        if cascade and count > 0:
            from bagels.models.record import Record
            from datetime import datetime

            linked_records = (
                session.query(Record).filter(Record.categoryId == category.id).all()
            )
            for record in linked_records:
                if record.deletedAt is None:
                    record.deletedAt = datetime.now()
            session.commit()

        delete_category(category.id)
        click.echo(f"Deleted category '{category.name}' (ID: {category.id})")
        if cascade and count > 0:
            click.echo(f"Soft-deleted {count} linked record(s).")

    finally:
        session.close()
        if engine is not None:
            engine.dispose()
