"""
Shared test fixtures for CLI testing.

Provides CliRunner, sample database with records, and quick access fixtures
for testing CLI query commands.
"""

import pytest
from click.testing import CliRunner
from datetime import datetime, timedelta
from pathlib import Path
import warnings
import yaml
import tempfile
import shutil
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import locations module for custom root management
from bagels.locations import set_custom_root, database_file

# Import config module (will use temp directory when set_custom_root is called)
from bagels.config import Config, config_file
import bagels.config as config_module

# Import models
from bagels.models.database.db import Base
from bagels.models.account import Account
from bagels.models.category import Category
from bagels.models.record import Record
from bagels.models.person import Person

# Import all models to ensure relationships are properly configured
from bagels.models import split  # noqa: F401


def _create_config_in_dir(tmpdir: str) -> None:
    """Create config file in the given directory."""
    config_path = Path(tmpdir) / "config" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(Config.get_default().model_dump(), f)


def _load_config() -> None:
    """Load config from the current custom root."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        config_module.CONFIG = Config()


@pytest.fixture
def cli_runner():
    """Click CliRunner instance for invoking commands."""
    return CliRunner()


@pytest.fixture
def sample_db_with_records():
    """
    Temporary file-based database with test data for CLI testing.

    Each test using this fixture gets its OWN isolated temp directory and database.
    No sharing between tests - prevents UNIQUE constraint failures.

    Creates:
    - 3 sample accounts (Savings, Checking, Credit Card)
    - 5 sample categories (Food, Transport, Entertainment nested hierarchically)
    - 20-30 sample records spanning 2-3 months

    Uses a temporary directory to ensure CLI commands use test database.
    """
    # Create a unique temp directory for this test
    tmpdir = tempfile.mkdtemp(prefix=f"bagels_cli_test_{uuid.uuid4().hex}_")

    # Set custom root at the START of the fixture
    set_custom_root(tmpdir)

    # Create config file AFTER setting custom root
    _create_config_in_dir(tmpdir)

    # Load config
    _load_config()

    # Create a NEW engine and session for this test's database
    # This is critical because the global db_engine is created at import time
    # and points to whatever database_file() returned then
    db_path = database_file()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    test_engine = create_engine(f"sqlite:///{db_path.resolve()}")
    TestSession = sessionmaker(bind=test_engine)

    # Create all tables
    Base.metadata.create_all(test_engine)

    # Create session
    session = TestSession()

    # Create accounts
    savings = Account(name="Savings", slug="savings", beginningBalance=5000.0)
    checking = Account(name="Checking", slug="checking", beginningBalance=2000.0)
    credit_card = Account(
        name="Credit Card", slug="credit-card", beginningBalance=-500.0
    )
    session.add_all([savings, checking, credit_card])
    session.flush()  # Flush to get IDs but don't commit yet

    # Create categories (hierarchical)
    from bagels.models.category import Nature

    food = Category(name="Food", slug="food", nature=Nature.NEED, color="#FF6B6B")
    session.add(food)
    session.flush()

    groceries = Category(
        name="Groceries",
        slug="groceries",
        nature=Nature.NEED,
        color="#FF6B6B",
        parentCategoryId=food.id,
    )
    restaurants = Category(
        name="Restaurants",
        slug="restaurants",
        nature=Nature.WANT,
        color="#FF6B6B",
        parentCategoryId=food.id,
    )
    transport = Category(
        name="Transport", slug="transport", nature=Nature.NEED, color="#4ECDC4"
    )
    entertainment = Category(
        name="Entertainment", slug="entertainment", nature=Nature.WANT, color="#95E1D3"
    )
    session.add_all([groceries, restaurants, transport, entertainment])
    session.flush()  # Flush to get IDs but don't commit yet

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
            # Include current month data (month_offset=0), then roll backward.
            record_date = base_date + timedelta(days=day - 1 - (month_offset * 30))

            # Alternate between different categories and accounts
            if day % 9 == 1:
                # Groceries records for category filter tests.
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

    # Ensure root "Food" category also has at least one record.
    records.append(
        Record(
            label="Food Root Record",
            amount=60.0,
            date=base_date + timedelta(days=2),
            accountId=savings.id,
            categoryId=food.id,
            isIncome=False,
            isTransfer=False,
        )
    )

    session.add_all(records)
    session.commit()

    yield session

    # Cleanup
    session.close()

    # Dispose of the engine to release file handles
    test_engine.dispose()

    # Remove the temp directory explicitly
    if Path(tmpdir).exists():
        shutil.rmtree(tmpdir, ignore_errors=True)


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
