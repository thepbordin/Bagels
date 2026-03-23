"""
Deprecated export CLI module.

YAML export command was removed as part of SQLite-only runtime reduction.
"""

import click

REMOVAL_MESSAGE = (
    "YAML export command was removed. Bagels now operates in SQLite-only mode."
)


@click.command()
def export_command() -> None:
    """Deprecated command kept only for import compatibility."""
    raise click.ClickException(REMOVAL_MESSAGE)
