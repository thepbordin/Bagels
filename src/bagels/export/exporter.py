"""
Export functions for Bagels entities to YAML format.

This module provides functions to export SQLAlchemy models to human-readable,
Git-friendly YAML files with dict-based structures and slug-based IDs.
"""

import yaml
from pathlib import Path
from sqlalchemy.orm import Session

from bagels.models.account import Account
from bagels.config import CONFIG


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
    if hasattr(account, 'slug') and account.slug:
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
            'name': account.name,
            'description': account.description,
            'beginningBalance': account.beginningBalance,
            'repaymentDate': account.repaymentDate,
            'hidden': account.hidden,
            'createdAt': account.createdAt.isoformat(),
            'updatedAt': account.updatedAt.isoformat()
        }

    # Write to YAML file
    output_path = output_dir / "accounts.yaml"
    with open(output_path, 'w') as f:
        yaml.safe_dump(
            {'accounts': accounts_dict},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
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
    account_slug = _generate_account_slug(account, account.session if hasattr(account, 'session') else None)

    accounts_dict = {
        account_slug: {
            'name': account.name,
            'description': account.description,
            'beginningBalance': account.beginningBalance,
            'repaymentDate': account.repaymentDate,
            'hidden': account.hidden,
            'createdAt': account.createdAt.isoformat(),
            'updatedAt': account.updatedAt.isoformat()
        }
    }

    # Write to YAML file
    output_path = output_dir / "accounts.yaml"
    with open(output_path, 'w') as f:
        yaml.safe_dump(
            {'accounts': accounts_dict},
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False
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
