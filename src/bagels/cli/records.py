"""
Records query commands for Bagels CLI.

Provides list and show commands for querying financial records with
comprehensive filtering capabilities, and batch import from YAML files.
"""

import click
from datetime import datetime
from pathlib import Path
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from sqlalchemy import create_engine
from sqlalchemy.orm import joinedload

from bagels.locations import database_file
from bagels.models.database.app import Session as AppSession, init_db
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

Session = AppSession


def _open_session():
    """Open session with current DB path while allowing tests to patch Session."""
    engine = None
    if hasattr(Session, "configure"):
        engine = create_engine(f"sqlite:///{database_file().resolve()}")
        Session.configure(bind=engine)
    session = Session()
    return session, engine


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
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
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
        if engine is not None:
            engine.dispose()


@records.command("show")
@click.argument("record_id", type=str)
@click.option(
    "--format", "-f", type=click.Choice(["table", "json", "yaml"]), default="table"
)
def show_record(record_id, format):
    """Show details for a single record."""
    from bagels.config import load_config

    load_config()
    init_db()

    session, engine = _open_session()
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
        if engine is not None:
            engine.dispose()


@records.command("add")
@click.option(
    "--yaml",
    "yaml",
    type=click.Path(exists=True),
    help="Import records from YAML file (batch mode)",
)
@click.option("--label", default=None, help="Record label/description")
@click.option(
    "--amount", "amount", type=float, default=None, help="Amount (must be > 0)"
)
@click.option("--date", "date", default=None, help="Date in YYYY-MM-DD format")
@click.option("--account-id", "account_id", type=int, default=None, help="Account ID")
@click.option(
    "--category-id",
    "category_id",
    type=int,
    default=None,
    help="Category ID (optional)",
)
@click.option(
    "--person-id", "person_id", type=int, default=None, help="Person ID (optional)"
)
@click.option("--income", is_flag=True, default=False, help="Mark as income record")
@click.option("--transfer", is_flag=True, default=False, help="Mark as transfer")
@click.option(
    "--transfer-to-account-id",
    "transfer_to_account_id",
    type=int,
    default=None,
    help="Destination account for transfers",
)
@click.option(
    "--format",
    "-f",
    "format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format for created record",
)
def add_record(
    yaml,
    label,
    amount,
    date,
    account_id,
    category_id,
    person_id,
    income,
    transfer,
    transfer_to_account_id,
    format,
):
    """Add a record (inline flags or batch --yaml import)."""
    from bagels.config import load_config
    from bagels.managers.records import create_record

    load_config()
    init_db()

    if not yaml:
        # Inline record creation
        if label is None:
            label = click.prompt("Record label")
        if amount is None:
            amount = click.prompt("Amount", type=float)
        if date is None:
            date = click.prompt(
                "Date (YYYY-MM-DD)", default=datetime.now().strftime("%Y-%m-%d")
            )
        if account_id is None:
            account_id = click.prompt("Account ID", type=int)

        # Validate date format
        try:
            record_date = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise click.ClickException(
                f"Invalid date format '{date}'. Expected YYYY-MM-DD"
            )

        session, engine = _open_session()
        try:
            # Validate account exists
            account = session.query(Account).filter(Account.id == account_id).first()
            if not account:
                raise click.ClickException(f"Account with ID {account_id} not found")

            # Validate optional FK references
            if category_id is not None:
                if (
                    not session.query(Category)
                    .filter(Category.id == category_id)
                    .first()
                ):
                    raise click.ClickException(
                        f"Category with ID {category_id} not found"
                    )

            if person_id is not None:
                if not session.query(Person).filter(Person.id == person_id).first():
                    raise click.ClickException(f"Person with ID {person_id} not found")

            if transfer and transfer_to_account_id is None:
                raise click.ClickException(
                    "--transfer-to-account-id required when --transfer is used"
                )

            if transfer_to_account_id is not None:
                if (
                    not session.query(Account)
                    .filter(Account.id == transfer_to_account_id)
                    .first()
                ):
                    raise click.ClickException(
                        f"Transfer destination account with ID {transfer_to_account_id} not found"
                    )

            # Build record data dict
            record_data = {
                "label": label,
                "amount": float(amount),
                "date": record_date,
                "accountId": account_id,
                "isIncome": income,
                "isTransfer": transfer,
            }
            if category_id is not None:
                record_data["categoryId"] = category_id
            if person_id is not None:
                record_data["personId"] = person_id
            if transfer_to_account_id is not None:
                record_data["transferToAccountId"] = transfer_to_account_id

            # Generate slug
            record_data["slug"] = generate_record_slug(record_date, session)

            # Create the record
            record = create_record(record_data)

            # Reload with eager-loaded relationships for formatting
            created = (
                session.query(Record)
                .options(
                    joinedload(Record.category),
                    joinedload(Record.account),
                    joinedload(Record.transferToAccount),
                )
                .filter(Record.id == record.id)
                .first()
            )

            output = format_records([created], format)
            click.echo(output)
        finally:
            session.close()
            if engine is not None:
                engine.dispose()
        return

    import yaml as yaml_module

    # Load YAML file
    yaml_path = Path(yaml)
    try:
        with open(yaml_path, "r") as f:
            yaml_data = yaml_module.safe_load(f)
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
    session, engine = _open_session()
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
        if engine is not None:
            engine.dispose()


@records.command("update")
@click.argument("identifier", type=str)
@click.option("--label", default=None, help="Record label/description")
@click.option("--amount", type=float, default=None, help="Amount (must be > 0)")
@click.option("--date", "date", default=None, help="Date in YYYY-MM-DD format")
@click.option("--account-id", "account_id", type=int, default=None, help="Account ID")
@click.option(
    "--category-id", "category_id", type=int, default=None, help="Category ID"
)
@click.option("--person-id", "person_id", type=int, default=None, help="Person ID")
@click.option(
    "--income/--no-income", "income", default=None, help="Mark as income or not"
)
@click.option(
    "--transfer/--no-transfer", "transfer", default=None, help="Mark as transfer or not"
)
@click.option(
    "--transfer-to-account-id",
    "transfer_to_account_id",
    type=int,
    default=None,
    help="Destination account for transfers",
)
@click.option(
    "--format",
    "-f",
    "format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
def update_record_cmd(
    identifier,
    label,
    amount,
    date,
    account_id,
    category_id,
    person_id,
    income,
    transfer,
    transfer_to_account_id,
    format,
):
    """Update an existing record by ID or slug."""
    from bagels.config import load_config
    from bagels.cli._helpers import resolve_entity
    from bagels.managers.records import update_record

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        record = resolve_entity(session, Record, identifier)
        if record is None:
            raise click.ClickException(f"Record '{identifier}' not found")

        # Build update dict from non-None options
        update_data = {}
        if label is not None:
            update_data["label"] = label
        if amount is not None:
            update_data["amount"] = amount
        if account_id is not None:
            update_data["accountId"] = account_id
        if category_id is not None:
            update_data["categoryId"] = category_id
        if person_id is not None:
            update_data["personId"] = person_id
        if income is not None:
            update_data["isIncome"] = income
        if transfer is not None:
            update_data["isTransfer"] = transfer
        if transfer_to_account_id is not None:
            update_data["transferToAccountId"] = transfer_to_account_id
        if date is not None:
            try:
                update_data["date"] = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise click.ClickException(
                    f"Invalid date format '{date}'. Expected YYYY-MM-DD"
                )

        if not update_data:
            raise click.ClickException(
                "No fields to update. Use --label, --amount, --date, --account-id, "
                "--category-id, --person-id, --income, or --transfer."
            )

        # Validate FK references if provided
        if account_id is not None:
            if not session.query(Account).filter(Account.id == account_id).first():
                raise click.ClickException(f"Account with ID {account_id} not found")
        if category_id is not None:
            if not session.query(Category).filter(Category.id == category_id).first():
                raise click.ClickException(f"Category with ID {category_id} not found")
        if person_id is not None:
            if not session.query(Person).filter(Person.id == person_id).first():
                raise click.ClickException(f"Person with ID {person_id} not found")
        if transfer_to_account_id is not None:
            if (
                not session.query(Account)
                .filter(Account.id == transfer_to_account_id)
                .first()
            ):
                raise click.ClickException(
                    f"Transfer destination account with ID {transfer_to_account_id} not found"
                )

        updated = update_record(record.id, update_data)

        # Reload with eager-loaded relationships for formatting
        reloaded = (
            session.query(Record)
            .options(
                joinedload(Record.category),
                joinedload(Record.account),
                joinedload(Record.transferToAccount),
            )
            .filter(Record.id == updated.id)
            .first()
        )

        output = format_records([reloaded], format)
        click.echo(output)

    finally:
        session.close()
        if engine is not None:
            engine.dispose()


@records.command("delete")
@click.argument("identifier", type=str)
@click.option("--force", is_flag=True, default=False, help="Skip confirmation prompt")
def delete_record_cmd(identifier, force):
    """Delete a record by ID or slug."""
    from bagels.config import load_config
    from bagels.cli._helpers import resolve_entity, confirm_delete
    from bagels.managers.records import delete_record

    load_config()
    init_db()

    session, engine = _open_session()
    try:
        record = resolve_entity(session, Record, identifier)
        if record is None:
            raise click.ClickException(f"Record '{identifier}' not found")

        date_str = record.date.strftime("%Y-%m-%d") if record.date else "no date"
        display_str = f"{record.label} (${record.amount:.2f}, {date_str})"

        if not confirm_delete("record", display_str, force):
            click.echo("Cancelled.", err=True)
            return

        record_id = record.id
        record_label = record.label
        delete_record(record_id)

        click.echo(f"Deleted record '{record_label}' (ID: {record_id})")

    finally:
        session.close()
        if engine is not None:
            engine.dispose()
