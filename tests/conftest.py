"""
Shared test fixtures for export/import testing.

Provides pytest fixtures for:
- In-memory SQLite database with clean state per test
- Temporary directories for YAML file operations
- Sample data fixtures for each entity type
- YAML file helper utilities
"""

import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from tempfile import mkdtemp

from bagels.models.database.db import Base
from bagels.models.account import Account
from bagels.models.category import Category
from bagels.models.person import Person
from bagels.models.record import Record
from bagels.models.record_template import RecordTemplate


# ---------- Database Fixtures ---------- #

@pytest.fixture(scope="function")
def in_memory_db():
    """
    Create an in-memory SQLite database with all tables.

    Returns:
        Session: SQLAlchemy session object
    """
    # Create in-memory SQLite engine
    engine = create_engine("sqlite:///:memory:")

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    # Clean up
    session.close()
    Base.metadata.drop_all(engine)


# ---------- Temporary Directory Fixtures ---------- #

@pytest.fixture(scope="function")
def temp_directory():
    """
    Create a temporary directory for YAML file operations.

    Returns:
        Path: Path object for temporary directory
    """
    temp_dir = Path(mkdtemp())
    yield temp_dir
    # Clean up is handled by tempfile.mkdtemp() context


# ---------- Sample Data Fixtures ---------- #

@pytest.fixture(scope="function")
def sample_account(in_memory_db):
    """
    Create a sample account for testing.

    Returns:
        Account: Account object with test data
    """
    account = Account(
        name="Savings",
        description="Emergency fund",
        beginningBalance=1000.0,
        repaymentDate=None,
        hidden=False
    )
    in_memory_db.add(account)
    in_memory_db.commit()
    return account


@pytest.fixture(scope="function")
def sample_category(in_memory_db):
    """
    Create a sample category for testing.

    Returns:
        Category: Category object with test data
    """
    category = Category(
        name="Groceries",
        parentId=None,
        nature="expense",
        color="#FF5733"
    )
    in_memory_db.add(category)
    in_memory_db.commit()
    return category


@pytest.fixture(scope="function")
def sample_person(in_memory_db):
    """
    Create a sample person for testing.

    Returns:
        Person: Person object with test data
    """
    person = Person(name="John Doe")
    in_memory_db.add(person)
    in_memory_db.commit()
    return person


@pytest.fixture(scope="function")
def sample_template(in_memory_db, sample_account, sample_category):
    """
    Create a sample record template for testing.

    Returns:
        RecordTemplate: RecordTemplate object with test data
    """
    template = RecordTemplate(
        label="Monthly Rent",
        amount=1500.0,
        accountId=sample_account.id,
        categoryId=sample_category.id,
        personId=None,
        isIncome=False,
        ordinal=0
    )
    in_memory_db.add(template)
    in_memory_db.commit()
    return template


@pytest.fixture(scope="function")
def sample_records(in_memory_db, sample_account, sample_category):
    """
    Create sample records for testing.

    Returns:
        list: List of 5 Record objects across different dates
    """
    records = []
    base_date = datetime(2026, 3, 1)

    for i in range(5):
        record = Record(
            label=f"Test Record {i+1}",
            amount=100.0 * (i + 1),
            date=base_date + timedelta(days=i),
            accountId=sample_account.id,
            categoryId=sample_category.id,
            isIncome=False,
            isTransfer=False
        )
        in_memory_db.add(record)
        records.append(record)

    in_memory_db.commit()
    return records


@pytest.fixture(scope="function")
def sample_category_tree(in_memory_db):
    """
    Create a sample category tree with parent-child relationships.

    Returns:
        dict: Dictionary with parent and child categories
    """
    # Parent category
    parent = Category(
        name="Food",
        parentId=None,
        nature="expense",
        color="#FF5733"
    )
    in_memory_db.add(parent)
    in_memory_db.flush()  # Get the ID without committing

    # Child category
    child = Category(
        name="Groceries",
        parentId=parent.id,
        nature="expense",
        color="#FF5733"
    )
    in_memory_db.add(child)

    # Grandchild category
    grandchild = Category(
        name="Weekly Groceries",
        parentId=child.id,
        nature="expense",
        color="#FF5733"
    )
    in_memory_db.add(grandchild)

    in_memory_db.commit()

    return {
        "parent": parent,
        "child": child,
        "grandchild": grandchild
    }


# ---------- YAML Helper Fixtures ---------- #

@pytest.fixture(scope="function")
def yaml_file(temp_directory):
    """
    Helper function to create YAML files in temp directory.

    Returns:
        callable: Function that writes YAML data and returns file path
    """
    def _create_yaml(filename, data):
        """
        Create a YAML file with the given data.

        Args:
            filename: Name of the file to create
            data: Dictionary data to write as YAML

        Returns:
            Path: Path to the created YAML file
        """
        import yaml

        file_path = temp_directory / filename
        with open(file_path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

        return file_path

    return _create_yaml


@pytest.fixture(scope="function")
def sample_yaml_data():
    """
    Provide sample YAML data structure for testing.

    Returns:
        dict: Sample YAML data with accounts, categories, etc.
    """
    return {
        "accounts": {
            "acc_savings": {
                "name": "Savings",
                "description": "Emergency fund",
                "beginningBalance": 1000.0,
                "repaymentDate": None,
                "hidden": False,
                "createdAt": "2026-03-14T10:30:00",
                "updatedAt": "2026-03-14T10:30:00"
            }
        },
        "categories": {
            "cat_groceries": {
                "name": "Groceries",
                "parentSlug": None,
                "nature": "expense",
                "color": "#FF5733",
                "createdAt": "2026-03-14T10:30:00",
                "updatedAt": "2026-03-14T10:30:00"
            }
        },
        "persons": {
            "person_john_doe": {
                "name": "John Doe",
                "createdAt": "2026-03-14T10:30:00",
                "updatedAt": "2026-03-14T10:30:00"
            }
        }
    }
