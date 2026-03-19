"""
Records query commands for Bagels CLI.

Provides list and show commands for querying financial records with
comprehensive filtering capabilities, and batch import from YAML files.
"""

import click
from datetime import datetime
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from sqlalchemy.orm import joinedload

from bagels.models.database.app import Session
from bagels.models.record import Record
from bagels.models.account import Account
from bagels.models.category import Category
from bagels.models.person import Person
from bagels.queries.formatters import format_records
from bagels.queries.filters import (
    apply_date_filters,
    apply_category_filter,
    apply_amount_filter,
    apply_account_filter,
    apply_person_filter,
)
from bagels.export.slug_generator import generate_record_slug


@click.group()
def records():
    """Query and manage records."""
    pass


@records.command("list")
@click.option("--category", "-c", help="Filter by category name")
@click.option("--month", "-m", help="Filter by month (YYYY-MM)")
@click.option("--date-from", help="Start date (YYYY-MM-DD)")
@click.option("--date-to", help="End date (YYYY-MM-DD)")
@click.option("--amount", help="Amount range (e.g., 100..500)")
@click.option("--account", "-a", help="Filter by account name")
@click.option("--person", "-p", help="Filter by person name")
@click.option(
    "--format", "-f", type=click.Choice(["table", "json", "yaml"]), default="table"
)
@click.option("--limit", type=int, default=50, help="Maximum records to display")
@click.option("--all", is_flag=True, help="Show all records (no limit)")
def list_records(
    category,
    month,
    date_from,
    date_to,
    amount,
    account,
    person,
    format,
    limit,
    all,
):
    """List records with optional filters."""
    session = Session()
    try:
        # Build query with eager loading
        query = (
            session.query(Record)
            .options(
                joinedload(Record.category),
                joinedload(Record.account),
                joinedload(Record.transferToAccount),
            )
            .filter(Record.transferToAccountId.is_(None))
        )

        # Apply filters
        try:
            query = apply_date_filters(query, month, date_from, date_to)
            query = apply_category_filter(query, category)
            query = apply_amount_filter(query, amount)
            query = apply_account_filter(query, account)
            query = apply_person_filter(query, person)
        except ValueError as e:
            raise click.ClickException(str(e))

        # Order by date descending
        query = query.order_by(Record.date.desc())

        # Apply limit (unless --all flag is set)
        if not all:
            query = query.limit(limit)
            limit_applied = limit
        else:
            limit_applied = None

        # Execute query
        records = query.all()

        # Show warning if limit was hit
        if limit_applied and len(records) == limit_applied:
            click.echo(
                click.style(
                    f"Showing {limit_applied} most recent records. Use --all to see all records.",
                    fg="yellow",
                )
            )
            click.echo()

        # Format and display output
        output = format_records(records, format)
        click.echo(output)

    finally:
        session.close()


@records.command("show")
@click.argument("record_id", type=str)
@click.option(
    "--format", "-f", type=click.Choice(["table", "json", "yaml"]), default="table"
)
def show_record(record_id, format):
    """Show details for a single record."""
    session = Session()
    try:
        # Try to parse as integer ID first, then as slug
        try:
            record_id_int = int(record_id)
            record = (
                session.query(Record)
                .options(
                    joinedload(Record.category),
                    joinedload(Record.account),
                    joinedload(Record.transferToAccount),
                )
                .filter(Record.id == record_id_int)
                .first()
            )
        except ValueError:
            # Not an integer, try as slug
            record = (
                session.query(Record)
                .options(
                    joinedload(Record.category),
                    joinedload(Record.account),
                    joinedload(Record.transferToAccount),
                )
                .filter(Record.slug == record_id)
                .first()
            )

        if not record:
            raise click.ClickException(f"Record '{record_id}' not found")

        # Format and display output
        output = format_records([record], format)
        click.echo(output)

    finally:
        session.close()


@records.command("add")
@click.option(
    "--from-yaml", type=click.Path(exists=True), help="Import records from YAML file"
)
def add_record(from_yaml):
    """Add records (batch import from YAML)."""
    if not from_yaml:
        raise click.ClickException(
            "Please provide --from-yaml option with a YAML file path"
        )

    import yaml

    # Load YAML file
    yaml_path = Path(from_yaml)
    try:
        with open(yaml_path, "r") as f:
            yaml_data = yaml.safe_load(f)
    except Exception as e:
        raise click.ClickException(f"Failed to load YAML file: {e}")

    # Normalize YAML data structure
    records_list = []
    if isinstance(yaml_data, list):
        # List format: [{label: ..., amount: ...}, ...]
        records_list = yaml_data
    elif isinstance(yaml_data, dict):
        # Dict with records key: {records: [{...}, ...]}
        if "records" in yaml_data:
            records_list = yaml_data["records"]
        else:
            # Dict format with record slugs as keys: {r_2026-03-14_001: {...}, ...}
            records_list = list(yaml_data.values())
    else:
        raise click.ClickException(
            "Invalid YAML format. Expected list or dict with records"
        )

    if not records_list:
        click.echo(click.style("No records found in YAML file", fg="yellow"))
        return

    # Validate and import records
    session = Session()
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            transient=False,
        ) as progress:
            validate_task = progress.add_task(
                "Validating records...", total=len(records_list)
            )

            validation_errors = []
            valid_records = []

            for idx, record_data in enumerate(records_list, 1):
                try:
                    # Validate required fields
                    required_fields = ["label", "amount", "date"]
                    missing_fields = [
                        f for f in required_fields if f not in record_data
                    ]

                    if missing_fields:
                        validation_errors.append(
                            f"Record {idx}: Missing required fields: {', '.join(missing_fields)}"
                        )
                        progress.update(validate_task, advance=1)
                        continue

                    # Validate date format
                    try:
                        record_date = datetime.strptime(record_data["date"], "%Y-%m-%d")
                    except ValueError:
                        validation_errors.append(
                            f"Record {idx}: Invalid date format '{record_data['date']}'. Expected YYYY-MM-DD"
                        )
                        progress.update(validate_task, advance=1)
                        continue

                    # Validate foreign keys
                    fk_errors = []

                    # Validate accountSlug
                    if "accountSlug" in record_data:
                        account = (
                            session.query(Account)
                            .filter(Account.slug == record_data["accountSlug"])
                            .first()
                        )
                        if not account:
                            fk_errors.append(
                                f"accountSlug '{record_data['accountSlug']}' not found"
                            )

                    # Validate categorySlug (optional)
                    if "categorySlug" in record_data:
                        category = (
                            session.query(Category)
                            .filter(Category.slug == record_data["categorySlug"])
                            .first()
                        )
                        if not category:
                            fk_errors.append(
                                f"categorySlug '{record_data['categorySlug']}' not found"
                            )

                    # Validate personSlug (optional)
                    if "personSlug" in record_data:
                        person = (
                            session.query(Person)
                            .filter(Person.slug == record_data["personSlug"])
                            .first()
                        )
                        if not person:
                            fk_errors.append(
                                f"personSlug '{record_data['personSlug']}' not found"
                            )

                    if fk_errors:
                        validation_errors.append(
                            f"Record {idx}: {', '.join(fk_errors)}"
                        )
                        progress.update(validate_task, advance=1)
                        continue

                    # Record is valid
                    valid_records.append(record_data)
                    progress.update(validate_task, advance=1)

                except Exception as e:
                    validation_errors.append(f"Record {idx}: Unexpected error: {e}")
                    progress.update(validate_task, advance=1)

            # Display validation results
            if validation_errors:
                progress.console.print(
                    click.style(
                        f"\n✗ Validation failed for {len(validation_errors)} record(s):",
                        fg="red",
                    )
                )
                for error in validation_errors[:10]:  # Show first 10 errors
                    progress.console.print(click.style(f"  • {error}", fg="red"))
                if len(validation_errors) > 10:
                    progress.console.print(
                        click.style(
                            f"  ... and {len(validation_errors) - 10} more errors",
                            fg="red",
                        )
                    )

                # Check if we have any valid records
                if not valid_records:
                    raise click.ClickException(
                        "No valid records to import. Please fix validation errors."
                    )

                # Ask if user wants to continue with valid records
                progress.console.print(
                    click.style(
                        f"\nFound {len(valid_records)} valid record(s).", fg="yellow"
                    )
                )
                if not click.confirm(
                    click.style("Continue importing valid records?", fg="yellow")
                ):
                    raise click.ClickException("Import cancelled by user")

            # Import valid records
            import_task = progress.add_task(
                "Importing records...", total=len(valid_records)
            )

            imported_count = 0
            batch_size = 100
            records_to_commit = []

            for record_data in valid_records:
                try:
                    # Resolve foreign keys
                    account = None
                    category = None
                    person = None

                    if "accountSlug" in record_data:
                        account = (
                            session.query(Account)
                            .filter(Account.slug == record_data["accountSlug"])
                            .first()
                        )

                    if "categorySlug" in record_data:
                        category = (
                            session.query(Category)
                            .filter(Category.slug == record_data["categorySlug"])
                            .first()
                        )

                    if "personSlug" in record_data:
                        person = (
                            session.query(Person)
                            .filter(Person.slug == record_data["personSlug"])
                            .first()
                        )

                    # Create record object
                    record_date = datetime.strptime(record_data["date"], "%Y-%m-%d")
                    record = Record(
                        label=record_data["label"],
                        amount=float(record_data["amount"]),
                        date=record_date,
                        accountId=account.id if account else None,
                        categoryId=category.id if category else None,
                        isIncome=record_data.get("isIncome", False),
                        isTransfer=record_data.get("isTransfer", False),
                    )

                    # Generate slug
                    record.slug = generate_record_slug(record_date, session)

                    session.add(record)
                    records_to_commit.append(record)
                    imported_count += 1

                    # Commit in batches
                    if len(records_to_commit) >= batch_size:
                        session.commit()
                        records_to_commit = []

                    progress.update(import_task, advance=1)

                except Exception as e:
                    validation_errors.append(
                        f"Failed to import record '{record_data.get('label', 'Unknown')}': {e}"
                    )
                    progress.update(import_task, advance=1)

            # Final commit for remaining records
            if records_to_commit:
                session.commit()

            # Display results
            progress.console.print()
            progress.console.print(
                click.style("✓ Import complete!", fg="green", bold=True)
            )
            progress.console.print(
                click.style(f"  Imported: {imported_count} record(s)", fg="green")
            )

            if validation_errors:
                progress.console.print()
                progress.console.print(
                    click.style(
                        f"⚠ {len(validation_errors)} error(s) during import:",
                        fg="yellow",
                    )
                )
                for error in validation_errors[:5]:
                    progress.console.print(click.style(f"  • {error}", fg="yellow"))

    finally:
        session.close()
