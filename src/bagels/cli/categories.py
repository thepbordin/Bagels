"""
Categories command group for CLI query commands.

Provides tree display of category hierarchies with multiple output formats.
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
from bagels.queries.formatters import to_json, to_yaml

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
