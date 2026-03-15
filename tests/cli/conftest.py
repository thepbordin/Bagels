"""
Shared test fixtures for CLI testing.

Provides CliRunner, sample database with records, and quick access fixtures
for testing CLI query commands.
"""

import pytest
from click.testing import CliRunner
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bagels.models.account import Account
from bagels.models.category import Category
from bagels.models.record import Record
from bagels.models.person import Person
from bagels.models.database.db import Base


@pytest.fixture
def cli_runner():
    """Click CliRunner instance for invoking commands."""
    return CliRunner()


@pytest.fixture
def in_memory_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def sample_db_with_records(in_memory_db):
    """
    In-memory database with test data for CLI testing.

    Creates:
    - 3 sample accounts (Savings, Checking, Credit Card)
    - 5 sample categories (Food, Transport, Entertainment nested hierarchically)
    - 20-30 sample records spanning 2-3 months
    """
    Session = sessionmaker(bind=in_memory_db)
    session = Session()

    # Create accounts
    savings = Account(
        name="Savings", accountType="asset", beginningBalance=5000.0, color="#00FF00"
    )
    checking = Account(
        name="Checking", accountType="asset", beginningBalance=2000.0, color="#0000FF"
    )
    credit_card = Account(
        name="Credit Card",
        accountType="liability",
        beginningBalance=-500.0,
        color="#FF0000",
    )
    session.add_all([savings, checking, credit_card])
    session.commit()

    # Create categories (hierarchical)
    food = Category(name="Food", nature="Need", color="#FF6B6B")
    groceries = Category(
        name="Groceries", nature="Need", color="#FF6B6B", parentId=food.id
    )
    restaurants = Category(
        name="Restaurants", nature="Want", color="#FF6B6B", parentId=food.id
    )
    transport = Category(name="Transport", nature="Need", color="#4ECDC4")
    entertainment = Category(name="Entertainment", nature="Want", color="#95E1D3")
    session.add_all([food, groceries, restaurants, transport, entertainment])
    session.commit()

    # Refresh to get IDs
    session.flush()
    session.refresh(groceries)
    session.refresh(restaurants)

    # Create records spanning 3 months
    base_date = datetime.now().replace(
        day=1, hour=12, minute=0, second=0, microsecond=0
    )

    records = []
    for month_offset in range(3):
        for day in range(1, 28, 3):  # Every 3 days
            record_date = base_date - timedelta(days=month_offset * 30 + (30 - day))

            # Alternate between different categories and accounts
            if day % 9 == 1:
                # Groceries
                record = Record(
                    label=f"Groceries - Day {day}",
                    amount=50.0 + (day % 5) * 10,
                    date=record_date,
                    accountId=savings.id,
                    categoryId=groceries.id,
                    isIncome=False,
                    isTransfer=False,
                )
            elif day % 9 == 4:
                # Restaurants
                record = Record(
                    label=f"Restaurant - Day {day}",
                    amount=30.0 + (day % 3) * 5,
                    date=record_date,
                    accountId=credit_card.id,
                    categoryId=restaurants.id,
                    isIncome=False,
                    isTransfer=False,
                )
            elif day % 9 == 7:
                # Transport
                record = Record(
                    label=f"Gas - Day {day}",
                    amount=40.0 + (day % 4) * 5,
                    date=record_date,
                    accountId=checking.id,
                    categoryId=transport.id,
                    isIncome=False,
                    isTransfer=False,
                )
            else:
                # Entertainment
                record = Record(
                    label=f"Movie - Day {day}",
                    amount=20.0 + (day % 2) * 10,
                    date=record_date,
                    accountId=credit_card.id,
                    categoryId=entertainment.id,
                    isIncome=False,
                    isTransfer=False,
                )

            records.append(record)

    session.add_all(records)
    session.commit()

    yield session

    session.close()


@pytest.fixture
def sample_accounts(sample_db_with_records):
    """Quick access to list of Account objects."""
    return sample_db_with_records.query(Account).all()


@pytest.fixture
def sample_categories(sample_db_with_records):
    """Quick access to list of Category objects."""
    return sample_db_with_records.query(Category).all()


@pytest.fixture
def sample_records(sample_db_with_records):
    """Quick access to list of Record objects."""
    return sample_db_with_records.query(Record).all()
