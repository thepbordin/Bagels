"""
Import CLI command for Bagels.

Provides the 'bagels import' command to import YAML files back into
SQLite database with validation and error handling.
"""

import click
from rich.progress import Progress, SpinnerColumn, TextColumn


@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.option('--dry-run', is_flag=True, help='Validate without importing')
def import_command(verbose: bool, dry_run: bool):
    """Import YAML files back into SQLite database."""
    from bagels.models.database.app import init_db, Session
    from bagels.importer.importer import (
        import_accounts_from_yaml,
        import_categories_from_yaml,
        import_persons_from_yaml,
        import_templates_from_yaml,
        import_records_from_yaml
    )
    from bagels.importer.validator import validate_yaml
    from bagels.locations import (
        yaml_accounts_path,
        yaml_categories_path,
        yaml_persons_path,
        yaml_templates_path,
        yaml_records_directory
    )
    import yaml

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Initializing database...", total=None)

        try:
            init_db()
            data_dir = yaml_accounts_path().parent
            session = Session()

            # Validate all YAML files first
            progress.update(task, description="Validating YAML files...")

            validation_errors = []

            # Validate accounts
            if yaml_accounts_path().exists():
                with open(yaml_accounts_path(), 'r') as f:
                    accounts_data = yaml.safe_load(f)
                is_valid, errors = validate_yaml(accounts_data, 'accounts', session=session)
                if not is_valid:
                    validation_errors.extend([f"accounts: {e}" for e in errors])

            # Validate categories
            if yaml_categories_path().exists():
                with open(yaml_categories_path(), 'r') as f:
                    categories_data = yaml.safe_load(f)
                is_valid, errors = validate_yaml(categories_data, 'categories', session=session)
                if not is_valid:
                    validation_errors.extend([f"categories: {e}" for e in errors])

            # Validate persons
            if yaml_persons_path().exists():
                with open(yaml_persons_path(), 'r') as f:
                    persons_data = yaml.safe_load(f)
                is_valid, errors = validate_yaml(persons_data, 'persons', session=session)
                if not is_valid:
                    validation_errors.extend([f"persons: {e}" for e in errors])

            # Validate templates
            if yaml_templates_path().exists():
                with open(yaml_templates_path(), 'r') as f:
                    templates_data = yaml.safe_load(f)
                is_valid, errors = validate_yaml(templates_data, 'templates', session=session)
                if not is_valid:
                    validation_errors.extend([f"templates: {e}" for e in errors])

            # Validate records
            if yaml_records_directory().exists():
                for yaml_file in sorted(yaml_records_directory().glob('*.yaml')):
                    with open(yaml_file, 'r') as f:
                        records_data = yaml.safe_load(f)
                    is_valid, errors = validate_yaml(records_data, 'records', session=session)
                    if not is_valid:
                        for e in errors:
                            validation_errors.append(f"{yaml_file.name}: {e}")

            if validation_errors:
                progress.update(task, description="Validation failed!")
                click.echo(click.style("✗ Validation failed:", fg="red"), err=True)
                for error in validation_errors:
                    click.echo(f"  • {error}", err=True)
                raise click.ClickException("Import aborted due to validation errors")

            if dry_run:
                progress.update(task, description="Dry run complete!", completed=True)
                click.echo(click.style("✓ Dry run complete - no errors found", fg="green"))
                return

            # Import accounts
            if yaml_accounts_path().exists():
                progress.update(task, description="Importing accounts...")
                with open(yaml_accounts_path(), 'r') as f:
                    accounts_data = yaml.safe_load(f)
                imported, updated = import_accounts_from_yaml(accounts_data, session=session)
                if verbose:
                    click.echo(f"  Accounts: {imported} imported, {updated} updated")

            # Import categories
            if yaml_categories_path().exists():
                progress.update(task, description="Importing categories...")
                with open(yaml_categories_path(), 'r') as f:
                    categories_data = yaml.safe_load(f)
                imported, updated = import_categories_from_yaml(categories_data, session=session)
                if verbose:
                    click.echo(f"  Categories: {imported} imported, {updated} updated")

            # Import persons
            if yaml_persons_path().exists():
                progress.update(task, description="Importing persons...")
                with open(yaml_persons_path(), 'r') as f:
                    persons_data = yaml.safe_load(f)
                imported, updated = import_persons_from_yaml(persons_data, session=session)
                if verbose:
                    click.echo(f"  Persons: {imported} imported, {updated} updated")

            # Import templates
            if yaml_templates_path().exists():
                progress.update(task, description="Importing templates...")
                with open(yaml_templates_path(), 'r') as f:
                    templates_data = yaml.safe_load(f)
                imported, updated = import_templates_from_yaml(templates_data, session=session)
                if verbose:
                    click.echo(f"  Templates: {imported} imported, {updated} updated")

            # Import records (all monthly files)
            if yaml_records_directory().exists():
                progress.update(task, description="Importing records...")
                total_imported = 0
                total_updated = 0
                for yaml_file in sorted(yaml_records_directory().glob('*.yaml')):
                    with open(yaml_file, 'r') as f:
                        records_data = yaml.safe_load(f)
                    imported, updated = import_records_from_yaml(records_data, session=session)
                    total_imported += imported
                    total_updated += updated
                if verbose:
                    click.echo(f"  Records: {total_imported} imported, {total_updated} updated")

            session.close()

            progress.update(task, description="Import complete!", completed=True)
            click.echo(click.style("✓ Import complete!", fg="green"))

        except Exception as e:
            progress.update(task, description=f"Import failed: {e}")
            raise click.ClickException(str(e))
