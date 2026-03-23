"""
Init CLI command for Bagels.

Provides the 'bagels init' command to initialize local directories and SQLite
database state for SQLite-only operation.
"""

import click


@click.command()
def init_command() -> None:
    """Initialize local Bagels config/data directories and SQLite database."""
    from bagels.config import load_config
    from bagels.locations import config_directory, data_directory, database_file
    from bagels.models.database.app import init_db

    try:
        cfg_dir = config_directory()
        data_dir = data_directory()
        load_config()
        init_db()

        click.echo(click.style("✓ Initialization complete!", fg="green"))
        click.echo("\nInitialized:")
        click.echo(f"  Config directory: {cfg_dir}")
        click.echo(f"  Data directory:   {data_dir}")
        click.echo(f"  Database file:    {database_file()}")
    except Exception as e:
        raise click.ClickException(f"Initialization failed: {str(e)}")
