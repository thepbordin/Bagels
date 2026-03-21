"""
YAML import functionality with merge-by-ID strategy.

Imports YAML files into SQLite database with validation, backup creation,
and referential integrity checks. YAML is authoritative - existing records
are updated if slugs match.

Requirements: DATA-06, DATA-08, FMT-01, FMT-02, FMT-03, FMT-05
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Tuple

from sqlalchemy.orm import Session

from bagels.importer.validator import ValidationError, validate_yaml

CONFLICT_MARKER = "<<<<<<< HEAD"


def _extract_entity_data(yaml_data: dict, entity_key: str) -> dict:
    """Accept wrapped ({entity: {...}}) and unwrapped ({slug: {...}}) formats."""
    if not isinstance(yaml_data, dict):
        return {}
    if entity_key in yaml_data and isinstance(yaml_data[entity_key], dict):
        return yaml_data[entity_key]
    return yaml_data


class ConflictError(Exception):
    """Raised when YAML files contain unresolved git conflict markers."""

    def __init__(self, conflicting_files: list[str]):
        self.conflicting_files = conflicting_files
        files_str = ", ".join(conflicting_files)
        super().__init__(
            f"Git conflict markers detected in: {files_str}. "
            "Resolve conflicts manually and re-run import."
        )


def check_for_conflict_markers(data_dir: Path) -> list[str]:
    """Scan all YAML files in data_dir for git conflict markers.

    Args:
        data_dir: Directory containing YAML files (accounts.yaml, records/*.yaml, etc.)

    Returns:
        List of relative file path strings that contain conflict markers.
        Empty list if no conflicts found.
    """
    conflicting: list[str] = []
    yaml_files: list[Path] = []

    # Collect all YAML files
    for name in ("accounts.yaml", "categories.yaml", "persons.yaml", "templates.yaml"):
        f = data_dir / name
        if f.exists():
            yaml_files.append(f)

    records_dir = data_dir / "records"
    if records_dir.is_dir():
        yaml_files.extend(sorted(records_dir.glob("*.yaml")))

    for yaml_file in yaml_files:
        try:
            content = yaml_file.read_text(encoding="utf-8")
            if CONFLICT_MARKER in content:
                conflicting.append(str(yaml_file.relative_to(data_dir)))
        except OSError:
            pass

    return conflicting


def create_backup() -> Path:
    """
    Create backup of current database before import.

    Returns:
        Path: Path to created backup file
    """
    from bagels.locations import backups_directory, database_file

    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.db"
    backup_path = backups_directory() / backup_filename

    # Copy database file
    db_path = database_file()
    if db_path.exists():
        shutil.copy2(db_path, backup_path)

    return backup_path


def import_accounts_from_yaml(yaml_data: dict, session: Session) -> Tuple[int, int]:
    """
    Import accounts from YAML using merge-by-ID strategy.

    Args:
        yaml_data: Parsed YAML data with accounts
        session: SQLAlchemy database session

    Returns:
        tuple: (imported_count, updated_count)

    Raises:
        ValidationError: If YAML validation fails
    """
    from bagels.models.account import Account

    imported_count = 0
    updated_count = 0

    # Create backup before importing
    create_backup()

    # Validate YAML first
    is_valid, errors = validate_yaml(yaml_data, "accounts", session)
    if not is_valid:
        raise ValidationError("YAML validation failed", errors)

    accounts_data = _extract_entity_data(yaml_data, "accounts")

    for slug, account_data in accounts_data.items():
        # Check if account exists
        existing = session.query(Account).filter(Account.slug == slug).first()

        if existing:
            # Update existing account (YAML is authoritative)
            for key, value in account_data.items():
                if key in ["createdAt", "updatedAt"]:
                    setattr(existing, key, datetime.fromisoformat(value))
                else:
                    setattr(existing, key, value)
            updated_count += 1
        else:
            # Create new account
            account = Account(slug=slug)
            for key, value in account_data.items():
                if key in ["createdAt", "updatedAt"]:
                    setattr(account, key, datetime.fromisoformat(value))
                else:
                    setattr(account, key, value)
            session.add(account)
            imported_count += 1

    session.commit()
    return imported_count, updated_count


def import_categories_from_yaml(yaml_data: dict, session: Session) -> Tuple[int, int]:
    """
    Import categories from YAML with parent-child relationships.

    Args:
        yaml_data: Parsed YAML data with categories
        session: SQLAlchemy database session

    Returns:
        tuple: (imported_count, updated_count)

    Raises:
        ValidationError: If YAML validation fails
    """
    from bagels.models.category import Category
    from bagels.models.category import Nature

    imported_count = 0
    updated_count = 0

    create_backup()
    is_valid, errors = validate_yaml(yaml_data, "categories", session)
    if not is_valid:
        raise ValidationError("YAML validation failed", errors)

    categories_data = _extract_entity_data(yaml_data, "categories")

    for slug, category_data in categories_data.items():
        existing = session.query(Category).filter(Category.slug == slug).first()

        if existing:
            # Update existing category
            for key, value in category_data.items():
                if key == "parentSlug":
                    # Resolve parentSlug to parent object
                    if value:
                        parent = (
                            session.query(Category)
                            .filter(Category.slug == value)
                            .first()
                        )
                        existing.parentCategoryId = parent.id if parent else None
                    else:
                        existing.parentCategoryId = None
                elif key in ["createdAt", "updatedAt"]:
                    setattr(existing, key, datetime.fromisoformat(value))
                elif key == "nature" and isinstance(value, str):
                    normalized = value.strip().lower()
                    legacy_map = {
                        "expense": Nature.NEED,
                        "income": Nature.WANT,
                        "need": Nature.NEED,
                        "want": Nature.WANT,
                        "must": Nature.MUST,
                    }
                    setattr(existing, key, legacy_map.get(normalized, value))
                else:
                    setattr(existing, key, value)
            updated_count += 1
        else:
            # Create new category
            category = Category(slug=slug)
            for key, value in category_data.items():
                if key == "parentSlug":
                    if value:
                        parent = (
                            session.query(Category)
                            .filter(Category.slug == value)
                            .first()
                        )
                        category.parentCategoryId = parent.id if parent else None
                elif key in ["createdAt", "updatedAt"]:
                    setattr(category, key, datetime.fromisoformat(value))
                elif key == "nature" and isinstance(value, str):
                    normalized = value.strip().lower()
                    legacy_map = {
                        "expense": Nature.NEED,
                        "income": Nature.WANT,
                        "need": Nature.NEED,
                        "want": Nature.WANT,
                        "must": Nature.MUST,
                    }
                    setattr(category, key, legacy_map.get(normalized, value))
                else:
                    setattr(category, key, value)
            session.add(category)
            imported_count += 1

    session.commit()
    return imported_count, updated_count


def import_persons_from_yaml(yaml_data: dict, session: Session) -> Tuple[int, int]:
    """
    Import persons from YAML using merge-by-ID strategy.

    Args:
        yaml_data: Parsed YAML data with persons
        session: SQLAlchemy database session

    Returns:
        tuple: (imported_count, updated_count)

    Raises:
        ValidationError: If YAML validation fails
    """
    from bagels.models.person import Person

    imported_count = 0
    updated_count = 0

    create_backup()
    is_valid, errors = validate_yaml(yaml_data, "persons", session)
    if not is_valid:
        raise ValidationError("YAML validation failed", errors)

    persons_data = _extract_entity_data(yaml_data, "persons")

    for slug, person_data in persons_data.items():
        existing = session.query(Person).filter(Person.slug == slug).first()

        if existing:
            # Update existing person
            for key, value in person_data.items():
                if key in ["createdAt", "updatedAt"]:
                    setattr(existing, key, datetime.fromisoformat(value))
                else:
                    setattr(existing, key, value)
            updated_count += 1
        else:
            # Create new person
            person = Person(slug=slug)
            for key, value in person_data.items():
                if key in ["createdAt", "updatedAt"]:
                    setattr(person, key, datetime.fromisoformat(value))
                else:
                    setattr(person, key, value)
            session.add(person)
            imported_count += 1

    session.commit()
    return imported_count, updated_count


def import_templates_from_yaml(yaml_data: dict, session: Session) -> Tuple[int, int]:
    """
    Import record templates from YAML using merge-by-ID strategy.

    Args:
        yaml_data: Parsed YAML data with templates
        session: SQLAlchemy database session

    Returns:
        tuple: (imported_count, updated_count)

    Raises:
        ValidationError: If YAML validation fails
    """
    from bagels.models.record_template import RecordTemplate

    imported_count = 0
    updated_count = 0

    create_backup()
    is_valid, errors = validate_yaml(yaml_data, "templates", session)
    if not is_valid:
        raise ValidationError("YAML validation failed", errors)

    templates_data = _extract_entity_data(yaml_data, "templates")

    for slug, template_data in templates_data.items():
        existing = (
            session.query(RecordTemplate).filter(RecordTemplate.slug == slug).first()
        )

        if existing:
            # Update existing template (YAML is authoritative)
            for key, value in template_data.items():
                if key == "accountSlug":
                    from bagels.models.account import Account

                    account = (
                        session.query(Account).filter(Account.slug == value).first()
                    )
                    if account:
                        existing.accountId = account.id
                elif key == "categorySlug" and value:
                    from bagels.models.category import Category

                    category = (
                        session.query(Category).filter(Category.slug == value).first()
                    )
                    if category:
                        existing.categoryId = category.id
                elif key == "personSlug" and value:
                    from bagels.models.person import Person

                    person = session.query(Person).filter(Person.slug == value).first()
                    if person:
                        existing.personId = person.id
                elif key == "ordinal":
                    setattr(existing, "order", value)
                elif key in ["createdAt", "updatedAt"]:
                    setattr(existing, key, datetime.fromisoformat(value))
                else:
                    setattr(existing, key, value)
            updated_count += 1
        else:
            # Create new template
            template = RecordTemplate(slug=slug)
            for key, value in template_data.items():
                if key == "accountSlug":
                    from bagels.models.account import Account

                    account = (
                        session.query(Account).filter(Account.slug == value).first()
                    )
                    if account:
                        template.accountId = account.id
                elif key == "categorySlug" and value:
                    from bagels.models.category import Category

                    category = (
                        session.query(Category).filter(Category.slug == value).first()
                    )
                    if category:
                        template.categoryId = category.id
                elif key == "personSlug" and value:
                    from bagels.models.person import Person

                    person = session.query(Person).filter(Person.slug == value).first()
                    if person:
                        template.personId = person.id
                elif key == "ordinal":
                    setattr(template, "order", value)
                elif key in ["createdAt", "updatedAt"]:
                    setattr(template, key, datetime.fromisoformat(value))
                else:
                    setattr(template, key, value)
            session.add(template)
            imported_count += 1

    session.commit()
    return imported_count, updated_count


def import_records_from_yaml(yaml_data: dict, session: Session) -> Tuple[int, int]:
    """
    Import records from YAML using merge-by-ID strategy.

    Args:
        yaml_data: Parsed YAML data with records
        session: SQLAlchemy database session

    Returns:
        tuple: (imported_count, updated_count)

    Raises:
        ValidationError: If YAML validation fails
    """
    from bagels.models.account import Account
    from bagels.models.category import Category
    from bagels.models.person import Person
    from bagels.models.record import Record

    imported_count = 0
    updated_count = 0

    create_backup()
    is_valid, errors = validate_yaml(yaml_data, "records", session)
    if not is_valid:
        raise ValidationError("YAML validation failed", errors)

    records_data = _extract_entity_data(yaml_data, "records")

    for slug, record_data in records_data.items():
        existing = session.query(Record).filter(Record.slug == slug).first()

        if existing:
            # Update existing record (YAML is authoritative)
            for key, value in record_data.items():
                if key == "accountSlug":
                    account = (
                        session.query(Account).filter(Account.slug == value).first()
                    )
                    if account:
                        existing.accountId = account.id
                elif key == "categorySlug" and value:
                    category = (
                        session.query(Category).filter(Category.slug == value).first()
                    )
                    if category:
                        existing.categoryId = category.id
                elif key == "personSlug" and value:
                    person = session.query(Person).filter(Person.slug == value).first()
                    if person:
                        existing.personId = person.id
                elif key == "transferToAccountSlug" and value:
                    account = (
                        session.query(Account).filter(Account.slug == value).first()
                    )
                    if account:
                        existing.transferToAccountId = account.id
                elif key in ["date", "createdAt", "updatedAt"]:
                    setattr(existing, key, datetime.fromisoformat(value))
                else:
                    setattr(existing, key, value)
            updated_count += 1
        else:
            # Create new record
            record = Record(slug=slug)
            for key, value in record_data.items():
                if key == "accountSlug":
                    account = (
                        session.query(Account).filter(Account.slug == value).first()
                    )
                    if account:
                        record.accountId = account.id
                elif key == "categorySlug" and value:
                    category = (
                        session.query(Category).filter(Category.slug == value).first()
                    )
                    if category:
                        record.categoryId = category.id
                elif key == "personSlug" and value:
                    person = session.query(Person).filter(Person.slug == value).first()
                    if person:
                        record.personId = person.id
                elif key == "transferToAccountSlug" and value:
                    account = (
                        session.query(Account).filter(Account.slug == value).first()
                    )
                    if account:
                        record.transferToAccountId = account.id
                elif key in ["date", "createdAt", "updatedAt"]:
                    setattr(record, key, datetime.fromisoformat(value))
                else:
                    setattr(record, key, value)
            session.add(record)
            imported_count += 1

    session.commit()
    return imported_count, updated_count


def run_full_import() -> None:
    """
    Import all YAML files from the data directory into SQLite.

    Reads accounts.yaml, categories.yaml, persons.yaml, templates.yaml, and
    all monthly record files (records/YYYY-MM.yaml) from data_directory().
    Missing files are silently skipped — the database is only updated for
    entities present in YAML.

    Requirements: DATA-08
    """
    import yaml as _yaml
    from sqlalchemy.orm import sessionmaker

    from bagels.locations import data_directory
    from bagels.models.database.app import db_engine

    data_dir = data_directory()

    # Check for git conflict markers before importing anything
    conflicting = check_for_conflict_markers(data_dir)
    if conflicting:
        raise ConflictError(conflicting)

    _Session = sessionmaker(bind=db_engine)
    session = _Session()

    try:
        # --- accounts ---
        accounts_file = data_dir / "accounts.yaml"
        if accounts_file.exists():
            with open(accounts_file) as f:
                yaml_data = _yaml.safe_load(f) or {}
            if _extract_entity_data(yaml_data, "accounts"):
                import_accounts_from_yaml(yaml_data, session)

        # --- categories ---
        categories_file = data_dir / "categories.yaml"
        if categories_file.exists():
            with open(categories_file) as f:
                yaml_data = _yaml.safe_load(f) or {}
            if _extract_entity_data(yaml_data, "categories"):
                import_categories_from_yaml(yaml_data, session)

        # --- persons ---
        persons_file = data_dir / "persons.yaml"
        if persons_file.exists():
            with open(persons_file) as f:
                yaml_data = _yaml.safe_load(f) or {}
            if _extract_entity_data(yaml_data, "persons"):
                import_persons_from_yaml(yaml_data, session)

        # --- templates ---
        templates_file = data_dir / "templates.yaml"
        if templates_file.exists():
            with open(templates_file) as f:
                yaml_data = _yaml.safe_load(f) or {}
            if _extract_entity_data(yaml_data, "templates"):
                import_templates_from_yaml(yaml_data, session)

        # --- records (monthly files) ---
        records_dir = data_dir / "records"
        if records_dir.is_dir():
            for record_file in sorted(records_dir.glob("*.yaml")):
                with open(record_file) as f:
                    yaml_data = _yaml.safe_load(f) or {}
                if _extract_entity_data(yaml_data, "records"):
                    import_records_from_yaml(yaml_data, session)

    finally:
        session.close()
