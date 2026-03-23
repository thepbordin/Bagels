"""
Deprecated git CLI module.

Git sync commands were removed as part of SQLite-only runtime reduction.
"""

import click

REMOVAL_MESSAGE = (
    "Git and YAML sync commands were removed. Bagels now operates in SQLite-only mode."
)


@click.group()
def git() -> None:
    """Deprecated command group kept only for import compatibility."""
    raise click.ClickException(REMOVAL_MESSAGE)
