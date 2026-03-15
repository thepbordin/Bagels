"""
Export functions for Bagels entities to YAML format.

This module provides functions to export SQLAlchemy models to human-readable,
Git-friendly YAML files with dict-based structures and slug-based IDs.
"""

import yaml
from collections import defaultdict
from pathlib import Path

from sqlalchemy.orm import Session

from bagels.export.slug_generator import generate_record_slug
from bagels.models.account import Account
from bagels.models.category import Category
from bagels.models.person import Person
from bagels.models.record import Record
from bagels.models.record_template import RecordTemplate


def _generate_account_slug(account: Account, session: Session = None) -> str:
    """
    Generate a slug for an account if it doesn't have one.

    Uses account name as base with number suffix for uniqueness.

    Args:
        account: Account instance
        session: SQLAlchemy session (optional, for uniqueness check)

    Returns:
        Slug string for the account
    """
    if hasattr(account, "slug") and account.slug:
        return account.slug

    # For now, use ID as fallback since slug is nullable
    # This will be improved when we implement proper slug generation
    return f"acc_{account.id}"


def export_accounts(session: Session, output_dir: Path) -> Path:
    """
    Export all accounts to a YAML file.

    Creates a dict structure keyed by account slug with all account fields
    including metadata timestamps.

    Args:
        session: SQLAlchemy session
        output_dir: Directory to write accounts.yaml

    Returns:
        Path to the created accounts.yaml file
    """
    # Query all accounts
    accounts = session.query(Account).all()

    # Build dict structure keyed by slug
    accounts_dict = {}
    for account in accounts:
        # Generate or get slug
        account_slug = _generate_account_slug(account, session)

        accounts_dict[account_slug] = {
            "name": account.name,
            "description": account.description,
            "beginningBalance": account.beginningBalance,
            "repaymentDate": account.repaymentDate,
            "hidden": account.hidden,
            "createdAt": account.createdAt.isoformat(),
            "updatedAt": account.updatedAt.isoformat(),
        }

    # Write to YAML file
    output_path = output_dir / "accounts.yaml"
    with open(output_path, "w") as f:
        yaml.safe_dump(
            {"accounts": accounts_dict},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    return output_path


def export_account_to_yaml(account: Account, output_dir: Path) -> Path:
    """
    Export a single account to YAML file (for testing).

    This is a convenience function for testing individual account export.

    Args:
        account: Account instance to export
        output_dir: Directory to write accounts.yaml

    Returns:
        Path to the created accounts.yaml file
    """
    # Generate or get slug
    account_slug = _generate_account_slug(
        account, account.session if hasattr(account, "session") else None
    )

    accounts_dict = {
        account_slug: {
            "name": account.name,
            "description": account.description,
            "beginningBalance": account.beginningBalance,
            "repaymentDate": account.repaymentDate,
            "hidden": account.hidden,
            "createdAt": account.createdAt.isoformat(),
            "updatedAt": account.updatedAt.isoformat(),
        }
    }

    # Write to YAML file
    output_path = output_dir / "accounts.yaml"
    with open(output_path, "w") as f:
        yaml.safe_dump(
            {"accounts": accounts_dict},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    return output_path


def export_all_accounts(session: Session, output_dir: Path) -> Path:
    """
    Export all accounts (alias for export_accounts for test compatibility).

    Args:
        session: SQLAlchemy session
        output_dir: Directory to write accounts.yaml

    Returns:
        Path to the created accounts.yaml file
    """
    return export_accounts(session, output_dir)


def export_categories(session: Session, output_dir: Path) -> Path:
    """
    Export all categories to a YAML file.

    Creates a dict structure keyed by category slug with parentSlug references.

    Args:
        session: SQLAlchemy session
        output_dir: Directory to write categories.yaml

    Returns:
        Path to the created categories.yaml file
    """
    categories = session.query(Category).all()

    categories_dict = {}
    for category in categories:
        category_slug = getattr(category, "slug", f"cat_{category.id}")

        categories_dict[category_slug] = {
            "name": category.name,
            "description": getattr(category, "description", None),
            "parentSlug": category.parentCategory.slug
            if category.parentCategory
            else None,
            "hidden": getattr(category, "hidden", False),
            "nature": category.nature.value,
            "color": category.color,
            "createdAt": category.createdAt.isoformat(),
            "updatedAt": category.updatedAt.isoformat(),
        }

    output_path = output_dir / "categories.yaml"
    with open(output_path, "w") as f:
        yaml.safe_dump(
            {"categories": categories_dict},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    return output_path


def export_category_to_yaml(
    category: Category, output_dir: Path, session: Session = None
) -> Path:
    """
    Export a single category to YAML file (for testing).

    Args:
        category: Category instance to export
        output_dir: Directory to write categories.yaml
        session: SQLAlchemy session

    Returns:
        Path to the created categories.yaml file
    """
    category_slug = getattr(category, "slug", f"cat_{category.id}")

    categories_dict = {
        category_slug: {
            "name": category.name,
            "description": getattr(category, "description", None),
            "parentSlug": category.parentCategory.slug
            if category.parentCategory
            else None,
            "hidden": getattr(category, "hidden", False),
            "nature": category.nature.value,
            "color": category.color,
            "createdAt": category.createdAt.isoformat(),
            "updatedAt": category.updatedAt.isoformat(),
        }
    }

    output_path = output_dir / "categories.yaml"
    with open(output_path, "w") as f:
        yaml.safe_dump(
            {"categories": categories_dict},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    return output_path


def export_all_categories(session: Session, output_dir: Path) -> Path:
    """
    Export all categories (alias for export_categories for test compatibility).

    Args:
        session: SQLAlchemy session
        output_dir: Directory to write categories.yaml

    Returns:
        Path to the created categories.yaml file
    """
    return export_categories(session, output_dir)
    """
    Export all categories to a YAML file.

    Creates a dict structure keyed by category slug with parentSlug references.

    Args:
        session: SQLAlchemy session
        output_dir: Directory to write categories.yaml

    Returns:
        Path to the created categories.yaml file
    """
    categories = session.query(Category).all()

    categories_dict = {}
    for category in categories:
        category_slug = getattr(category, "slug", f"cat_{category.id}")

        categories_dict[category_slug] = {
            "name": category.name,
            "description": getattr(category, "description", None),
            "parentSlug": category.parentCategory.slug
            if category.parentCategory
            else None,
            "hidden": getattr(category, "hidden", False),
            "nature": category.nature.value,
            "color": category.color,
            "createdAt": category.createdAt.isoformat(),
            "updatedAt": category.updatedAt.isoformat(),
        }

    output_path = output_dir / "categories.yaml"
    with open(output_path, "w") as f:
        yaml.safe_dump(
            {"categories": categories_dict},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    return output_path


def export_person_to_yaml(person: Person, output_dir: Path) -> Path:
    """
    Export a single person to YAML file (for testing).

    Args:
        person: Person instance to export
        output_dir: Directory to write persons.yaml

    Returns:
        Path to the created persons.yaml file
    """
    person_slug = getattr(person, "slug", f"person_{person.id}")

    persons_dict = {
        person_slug: {
            "name": person.name,
            "createdAt": person.createdAt.isoformat(),
            "updatedAt": person.updatedAt.isoformat(),
        }
    }

    output_path = output_dir / "persons.yaml"
    with open(output_path, "w") as f:
        yaml.safe_dump(
            {"persons": persons_dict},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    return output_path


def export_all_persons(session: Session, output_dir: Path) -> Path:
    """
    Export all persons (alias for export_persons for test compatibility).

    Args:
        session: SQLAlchemy session
        output_dir: Directory to write persons.yaml

    Returns:
        Path to the created persons.yaml file
    """
    return export_persons(session, output_dir)


def export_persons(session: Session, output_dir: Path) -> Path:
    """
    Export all persons to a YAML file.

    Args:
        session: SQLAlchemy session
        output_dir: Directory to write persons.yaml

    Returns:
        Path to the created persons.yaml file
    """
    persons = session.query(Person).all()

    persons_dict = {}
    for person in persons:
        person_slug = getattr(person, "slug", f"person_{person.id}")

        persons_dict[person_slug] = {
            "name": person.name,
            "createdAt": person.createdAt.isoformat(),
            "updatedAt": person.updatedAt.isoformat(),
        }

    output_path = output_dir / "persons.yaml"
    with open(output_path, "w") as f:
        yaml.safe_dump(
            {"persons": persons_dict},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    return output_path


def export_template_to_yaml(template: RecordTemplate, output_dir: Path) -> Path:
    """
    Export a single template to YAML file (for testing).

    Args:
        template: RecordTemplate instance to export
        output_dir: Directory to write templates.yaml

    Returns:
        Path to the created templates.yaml file
    """
    template_slug = getattr(template, "slug", f"tpl_{template.id}")

    templates_dict = {
        template_slug: {
            "label": template.label,
            "amount": template.amount,
            "accountSlug": template.account.slug
            if template.account
            and hasattr(template.account, "slug")
            and template.account.slug
            else f"acc_{template.accountId}"
            if template.account
            else None,
            "categorySlug": template.category.slug
            if template.category
            and hasattr(template.category, "slug")
            and template.category.slug
            else f"cat_{template.categoryId}"
            if template.category
            else None,
            "personSlug": None,
            "isIncome": template.isIncome,
            "isTransfer": template.isTransfer,
            "order": template.order,
            "createdAt": template.createdAt.isoformat(),
            "updatedAt": template.updatedAt.isoformat(),
        }
    }

    output_path = output_dir / "templates.yaml"
    with open(output_path, "w") as f:
        yaml.safe_dump(
            {"templates": templates_dict},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    return output_path


def export_all_templates(session: Session, output_dir: Path) -> Path:
    """
    Export all templates (alias for export_templates for test compatibility).

    Args:
        session: SQLAlchemy session
        output_dir: Directory to write templates.yaml

    Returns:
        Path to the created templates.yaml file
    """
    return export_templates(session, output_dir)


def export_templates(session: Session, output_dir: Path) -> Path:
    """
    Export all record templates to a YAML file.

    Args:
        session: SQLAlchemy session
        output_dir: Directory to write templates.yaml

    Returns:
        Path to the created templates.yaml file
    """
    templates = session.query(RecordTemplate).order_by(RecordTemplate.order).all()

    templates_dict = {}
    for template in templates:
        template_slug = getattr(template, "slug", f"tpl_{template.id}")

        templates_dict[template_slug] = {
            "label": template.label,
            "amount": template.amount,
            "accountSlug": template.account.slug
            if template.account
            and hasattr(template.account, "slug")
            and template.account.slug
            else f"acc_{template.accountId}"
            if template.account
            else None,
            "categorySlug": template.category.slug
            if template.category
            and hasattr(template.category, "slug")
            and template.category.slug
            else f"cat_{template.categoryId}"
            if template.category
            else None,
            "personSlug": None,  # Template doesn't have person relationship
            "isIncome": template.isIncome,
            "isTransfer": template.isTransfer,
            "order": template.order,
            "createdAt": template.createdAt.isoformat(),
            "updatedAt": template.updatedAt.isoformat(),
        }

    output_path = output_dir / "templates.yaml"
    with open(output_path, "w") as f:
        yaml.safe_dump(
            {"templates": templates_dict},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    return output_path


def export_records_for_month(
    session: Session, output_dir: Path, year: int, month: int
) -> Path:
    """Export all records for a specific month to a YAML file.

    Writes the records/YYYY-MM.yaml file even if no records exist for
    the given month (writes an empty records dict to prevent stale data).

    Args:
        session: SQLAlchemy session
        output_dir: Directory under which records/ subdirectory is created
        year: Four-digit year (e.g. 2026)
        month: Month number 1-12

    Returns:
        Path to the written YYYY-MM.yaml file
    """
    from datetime import datetime

    start_date = datetime(year, month, 1)
    # Compute the first day of the next month to use as exclusive upper bound
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    records = (
        session.query(Record)
        .filter(Record.date >= start_date, Record.date < end_date)
        .order_by(Record.date)
        .all()
    )

    records_dict: dict = {}
    for record in records:
        if not getattr(record, "slug", None):
            record.slug = generate_record_slug(record.date, session)

        record_data = {
            "label": record.label,
            "amount": record.amount,
            "date": record.date.isoformat(),
            "accountSlug": (
                record.account.slug
                if record.account and getattr(record.account, "slug", None)
                else f"acc_{record.accountId}"
                if record.account
                else None
            ),
            "categorySlug": (
                record.category.slug
                if record.category and getattr(record.category, "slug", None)
                else f"cat_{record.categoryId}"
                if record.category
                else None
            ),
            "personSlug": None,
            "isIncome": record.isIncome,
            "isTransfer": record.isTransfer,
            "transferToAccountSlug": (
                record.transferToAccount.slug
                if record.transferToAccount
                and getattr(record.transferToAccount, "slug", None)
                else (
                    f"acc_{record.transferToAccountId}"
                    if record.transferToAccount
                    else None
                )
            ),
            "slug": record.slug,
            "createdAt": record.createdAt.isoformat(),
            "updatedAt": record.updatedAt.isoformat(),
        }
        records_dict[record.slug] = record_data

    records_dir = output_dir / "records"
    records_dir.mkdir(exist_ok=True, parents=True)

    month_key = f"{year:04d}-{month:02d}"
    filepath = records_dir / f"{month_key}.yaml"
    with open(filepath, "w") as f:
        yaml.safe_dump(
            {"records": records_dict},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    return filepath


def export_records_by_month(session: Session, output_dir: Path) -> Path:
    """
    Export all records grouped by month to separate YAML files.

    Args:
        session: SQLAlchemy session
        output_dir: Directory to write monthly record files

    Returns:
        Path to the records directory
    """
    records = session.query(Record).all()

    # Group records by month
    monthly_records = defaultdict(list)
    for record in records:
        month_key = record.date.strftime("%Y-%m")
        monthly_records[month_key].append(record)

    records_dir = output_dir / "records"
    records_dir.mkdir(exist_ok=True, parents=True)

    for month, records in monthly_records.items():
        records_dict = {}
        for record in records:
            # Generate slug if doesn't exist
            if not hasattr(record, "slug") or not record.slug:
                record.slug = generate_record_slug(record.date, session)

            record_data = {
                "label": record.label,
                "amount": record.amount,
                "date": record.date.isoformat(),
                "accountSlug": record.account.slug
                if record.account
                and hasattr(record.account, "slug")
                and record.account.slug
                else f"acc_{record.accountId}"
                if record.account
                else None,
                "categorySlug": record.category.slug
                if record.category
                and hasattr(record.category, "slug")
                and record.category.slug
                else f"cat_{record.categoryId}"
                if record.category
                else None,
                "personSlug": None,
                "isIncome": record.isIncome,
                "isTransfer": record.isTransfer,
                "transferToAccountSlug": record.transferToAccount.slug
                if record.transferToAccount
                and hasattr(record.transferToAccount, "slug")
                and record.transferToAccount.slug
                else f"acc_{record.transferToAccountId}"
                if record.transferToAccount
                else None,
                "slug": record.slug,
                "createdAt": record.createdAt.isoformat(),
                "updatedAt": record.updatedAt.isoformat(),
            }
            records_dict[record.slug] = record_data

        # Write to monthly file
        filename = f"{month}.yaml"
        filepath = records_dir / filename
        with open(filepath, "w") as f:
            yaml.safe_dump(
                {"records": records_dict},
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    return records_dir
