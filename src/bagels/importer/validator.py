"""
YAML validation for import functionality.

Validates YAML structure, required fields, data types, and referential integrity
before importing to prevent partial imports and data corruption.

Requirements: FMT-01, FMT-02, FMT-03, FMT-04, FMT-05
"""

import re
from datetime import datetime
from typing import Any, Dict, Tuple


class ValidationError(Exception):
    """Custom exception for validation errors with detailed error list."""

    def __init__(self, message: str, errors: list[str]):
        self.message = message
        self.errors = errors
        super().__init__(f"{message}: {', '.join(errors)}")


def validate_yaml(yaml_data: dict, entity_type: str, session) -> tuple[bool, list[str]]:
    """
    Router function that calls specific validator based on entity_type.

    Args:
        yaml_data: Parsed YAML data as dictionary
        entity_type: Type of entity ('accounts', 'categories', 'records', 'persons', 'templates')
        session: SQLAlchemy database session for foreign key validation

    Returns:
        tuple: (is_valid, errors_list)
    """
    validators = {
        'accounts': validate_accounts_yaml,
        'categories': lambda data: validate_categories_yaml(data, session),
        'records': lambda data: validate_records_yaml(data, session),
        'persons': validate_persons_yaml,
        'templates': lambda data: validate_templates_yaml(data, session),
    }

    validator = validators.get(entity_type)
    if not validator:
        return False, [f"Unknown entity type: {entity_type}"]

    return validator(yaml_data)


def validate_accounts_yaml(yaml_data: dict) -> tuple[bool, list[str]]:
    """
    Validate accounts YAML structure and data types.

    Checks:
    - Top-level 'accounts' key exists
    - Required fields present (name, beginningBalance, hidden, createdAt, updatedAt)
    - Timestamp format is ISO 8601
    - Monetary values are numeric

    Args:
        yaml_data: Parsed YAML data

    Returns:
        tuple: (is_valid, errors_list)
    """
    errors = []

    # Check top-level structure
    if 'accounts' not in yaml_data:
        return False, ["Missing required key: 'accounts'"]

    accounts = yaml_data['accounts']

    # Validate each account
    for slug, account_data in accounts.items():
        # Check required fields
        required_fields = ['name', 'beginningBalance', 'hidden', 'createdAt', 'updatedAt']
        for field in required_fields:
            if field not in account_data:
                errors.append(f"accounts.{slug}: Missing required field '{field}'")

        # Validate timestamp format
        for ts_field in ['createdAt', 'updatedAt']:
            if ts_field in account_data:
                try:
                    datetime.fromisoformat(account_data[ts_field])
                except (ValueError, TypeError):
                    errors.append(f"accounts.{slug}: Invalid timestamp format for '{ts_field}'")

        # Validate monetary value
        if 'beginningBalance' in account_data:
            if not isinstance(account_data['beginningBalance'], (int, float)):
                errors.append(f"accounts.{slug}: beginningBalance must be a number")

    return len(errors) == 0, errors


def validate_categories_yaml(yaml_data: dict, session) -> tuple[bool, list[str]]:
    """
    Validate categories YAML structure and data types.

    Checks:
    - Top-level 'categories' key exists
    - Required fields present
    - Parent category references exist (if specified)
    - Timestamp format is ISO 8601

    Args:
        yaml_data: Parsed YAML data
        session: SQLAlchemy session for foreign key validation

    Returns:
        tuple: (is_valid, errors_list)
    """
    from bagels.models.category import Category

    errors = []

    if 'categories' not in yaml_data:
        return False, ["Missing required key: 'categories'"]

    categories = yaml_data['categories']

    for slug, category_data in categories.items():
        # Check required fields
        required_fields = ['name', 'nature', 'color', 'createdAt', 'updatedAt']
        for field in required_fields:
            if field not in category_data:
                errors.append(f"categories.{slug}: Missing required field '{field}'")

        # Validate parent reference
        if 'parentSlug' in category_data and category_data['parentSlug']:
            parent_slug = category_data['parentSlug']
            parent = session.query(Category).filter(Category.slug == parent_slug).first()
            if not parent:
                errors.append(f"categories.{slug}: Referenced parent category '{parent_slug}' does not exist")

        # Validate timestamps
        for ts_field in ['createdAt', 'updatedAt']:
            if ts_field in category_data:
                try:
                    datetime.fromisoformat(category_data[ts_field])
                except (ValueError, TypeError):
                    errors.append(f"categories.{slug}: Invalid timestamp format for '{ts_field}'")

    return len(errors) == 0, errors


def validate_records_yaml(yaml_data: dict, session) -> tuple[bool, list[str]]:
    """
    Validate records YAML structure and data types.

    Checks:
    - Top-level 'records' key exists
    - Slug format matches r_YYYY-MM-DD_### pattern
    - Required fields present
    - Foreign key references exist (account, category, person)
    - Timestamp and date format is ISO 8601
    - Amount is numeric

    Args:
        yaml_data: Parsed YAML data
        session: SQLAlchemy session for foreign key validation

    Returns:
        tuple: (is_valid, errors_list)
    """
    from bagels.models.account import Account
    from bagels.models.category import Category
    from bagels.models.person import Person

    errors = []

    if 'records' not in yaml_data:
        return False, ["Missing required key: 'records'"]

    records = yaml_data['records']

    # Slug format regex: r_YYYY-MM-DD_###
    slug_pattern = re.compile(r'^r_\d{4}-\d{2}-\d{2}_\d{3}$')

    for slug, record_data in records.items():
        # Validate slug format
        if not slug_pattern.match(slug):
            errors.append(f"records.{slug}: Invalid slug format (expected r_YYYY-MM-DD_###)")

        # Check required fields
        required_fields = ['label', 'amount', 'date', 'accountSlug', 'isIncome', 'isTransfer', 'createdAt', 'updatedAt']
        for field in required_fields:
            if field not in record_data:
                errors.append(f"records.{slug}: Missing required field '{field}'")

        # Validate account reference
        if 'accountSlug' in record_data:
            account_slug = record_data['accountSlug']
            account = session.query(Account).filter(Account.slug == account_slug).first()
            if not account:
                errors.append(f"records.{slug}: Referenced account '{account_slug}' does not exist")

        # Validate category reference (if provided)
        if 'categorySlug' in record_data and record_data['categorySlug']:
            category_slug = record_data['categorySlug']
            category = session.query(Category).filter(Category.slug == category_slug).first()
            if not category:
                errors.append(f"records.{slug}: Referenced category '{category_slug}' does not exist")

        # Validate person reference (if provided)
        if 'personSlug' in record_data and record_data['personSlug']:
            person_slug = record_data['personSlug']
            person = session.query(Person).filter(Person.slug == person_slug).first()
            if not person:
                errors.append(f"records.{slug}: Referenced person '{person_slug}' does not exist")

        # Validate transfer destination account (if provided)
        if 'transferToAccountSlug' in record_data and record_data['transferToAccountSlug']:
            transfer_slug = record_data['transferToAccountSlug']
            transfer_account = session.query(Account).filter(Account.slug == transfer_slug).first()
            if not transfer_account:
                errors.append(f"records.{slug}: Referenced transfer destination account '{transfer_slug}' does not exist")

        # Validate amount is numeric
        if 'amount' in record_data:
            if not isinstance(record_data['amount'], (int, float)):
                errors.append(f"records.{slug}: Amount must be a number")

        # Validate date format
        if 'date' in record_data:
            try:
                datetime.fromisoformat(record_data['date'])
            except (ValueError, TypeError):
                errors.append(f"records.{slug}: Invalid date format for 'date'")

        # Validate timestamps
        for ts_field in ['createdAt', 'updatedAt']:
            if ts_field in record_data:
                try:
                    datetime.fromisoformat(record_data[ts_field])
                except (ValueError, TypeError):
                    errors.append(f"records.{slug}: Invalid timestamp format for '{ts_field}'")

    return len(errors) == 0, errors


def validate_persons_yaml(yaml_data: dict) -> tuple[bool, list[str]]:
    """
    Validate persons YAML structure and data types.

    Checks:
    - Top-level 'persons' key exists
    - Required fields present (name, createdAt, updatedAt)
    - Timestamp format is ISO 8601

    Args:
        yaml_data: Parsed YAML data

    Returns:
        tuple: (is_valid, errors_list)
    """
    errors = []

    if 'persons' not in yaml_data:
        return False, ["Missing required key: 'persons'"]

    persons = yaml_data['persons']

    for slug, person_data in persons.items():
        # Check required fields
        required_fields = ['name', 'createdAt', 'updatedAt']
        for field in required_fields:
            if field not in person_data:
                errors.append(f"persons.{slug}: Missing required field '{field}'")

        # Validate timestamps
        for ts_field in ['createdAt', 'updatedAt']:
            if ts_field in person_data:
                try:
                    datetime.fromisoformat(person_data[ts_field])
                except (ValueError, TypeError):
                    errors.append(f"persons.{slug}: Invalid timestamp format for '{ts_field}'")

    return len(errors) == 0, errors


def validate_templates_yaml(yaml_data: dict, session) -> tuple[bool, list[str]]:
    """
    Validate record templates YAML structure and data types.

    Checks:
    - Top-level 'templates' key exists
    - Required fields present
    - Foreign key references exist (account, category, person)
    - Amount is numeric
    - Timestamp format is ISO 8601

    Args:
        yaml_data: Parsed YAML data
        session: SQLAlchemy session for foreign key validation

    Returns:
        tuple: (is_valid, errors_list)
    """
    from bagels.models.account import Account
    from bagels.models.category import Category
    from bagels.models.person import Person

    errors = []

    if 'templates' not in yaml_data:
        return False, ["Missing required key: 'templates'"]

    templates = yaml_data['templates']

    for slug, template_data in templates.items():
        # Check required fields
        required_fields = ['label', 'amount', 'accountSlug', 'isIncome', 'ordinal', 'createdAt', 'updatedAt']
        for field in required_fields:
            if field not in template_data:
                errors.append(f"templates.{slug}: Missing required field '{field}'")

        # Validate account reference
        if 'accountSlug' in template_data:
            account_slug = template_data['accountSlug']
            account = session.query(Account).filter(Account.slug == account_slug).first()
            if not account:
                errors.append(f"templates.{slug}: Referenced account '{account_slug}' does not exist")

        # Validate category reference (if provided)
        if 'categorySlug' in template_data and template_data['categorySlug']:
            category_slug = template_data['categorySlug']
            category = session.query(Category).filter(Category.slug == category_slug).first()
            if not category:
                errors.append(f"templates.{slug}: Referenced category '{category_slug}' does not exist")

        # Validate person reference (if provided)
        if 'personSlug' in template_data and template_data['personSlug']:
            person_slug = template_data['personSlug']
            person = session.query(Person).filter(Person.slug == person_slug).first()
            if not person:
                errors.append(f"templates.{slug}: Referenced person '{person_slug}' does not exist")

        # Validate amount is numeric
        if 'amount' in template_data:
            if not isinstance(template_data['amount'], (int, float)):
                errors.append(f"templates.{slug}: Amount must be a number")

        # Validate timestamps
        for ts_field in ['createdAt', 'updatedAt']:
            if ts_field in template_data:
                try:
                    datetime.fromisoformat(template_data[ts_field])
                except (ValueError, TypeError):
                    errors.append(f"templates.{slug}: Invalid timestamp format for '{ts_field}'")

    return len(errors) == 0, errors
