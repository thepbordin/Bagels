"""
Deprecated import CLI module.

YAML import command was removed as part of SQLite-only runtime reduction.
"""

import click

REMOVAL_MESSAGE = (
    "YAML import command was removed. Bagels now operates in SQLite-only mode."
)


@click.command()
def import_command() -> None:
    """Deprecated command kept only for import compatibility."""
    raise click.ClickException(REMOVAL_MESSAGE)
