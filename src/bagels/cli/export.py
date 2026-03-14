"""
Export CLI command for Bagels.

Provides the 'bagels export' command to export all SQLite entities
to YAML files with progress bars and user-friendly output.
"""

import click
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path


@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def export_command(verbose: bool):
    """Export all SQLite entities to YAML files."""
    from bagels.models.database.app import init_db, Session
    from bagels.export.exporter import (
        export_accounts,
        export_categories,
        export_persons,
        export_templates,
        export_records_by_month
    )
    from bagels.locations import data_directory

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Initializing database...", total=None)

        try:
            # Initialize database
            init_db()
            data_dir = data_directory()

            # Create session for export operations
            session = Session()

            # Export accounts
            progress.update(task, description="Exporting accounts...")
            accounts_path = export_accounts(session=session, output_dir=data_dir)
            if verbose:
                click.echo(f"  Accounts: {accounts_path}")

            # Export categories
            progress.update(task, description="Exporting categories...")
            categories_path = export_categories(session=session, output_dir=data_dir)
            if verbose:
                click.echo(f"  Categories: {categories_path}")

            # Export persons
            progress.update(task, description="Exporting persons...")
            persons_path = export_persons(session=session, output_dir=data_dir)
            if verbose:
                click.echo(f"  Persons: {persons_path}")

            # Export templates
            progress.update(task, description="Exporting templates...")
            templates_path = export_templates(session=session, output_dir=data_dir)
            if verbose:
                click.echo(f"  Templates: {templates_path}")

            # Export records
            progress.update(task, description="Exporting records...")
            records_count = export_records_by_month(session=session, output_dir=data_dir)
            if verbose:
                click.echo(f"  Records: {records_count} monthly files")

            session.close()

            progress.update(task, description="Export complete!", completed=True)
            click.echo(click.style("✓ Export complete!", fg="green"))

        except Exception as e:
            progress.update(task, description=f"Export failed: {e}")
            raise click.ClickException(str(e))
