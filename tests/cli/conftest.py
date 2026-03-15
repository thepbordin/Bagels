"""
Shared test fixtures for CLI command testing.

Provides pytest fixtures for:
- Click CliRunner for CLI command invocation
- Sample database with comprehensive test data
- Quick access fixtures for accounts, categories, records
- Session fixture for CLI test queries
"""

import pytest
from click.testing import CliRunner
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Initialize config BEFORE importing models
from bagels.config import Config, config_file
import bagels.config as config_module
import yaml
import warnings

# Create config file if needed
if not config_file().exists():
    config_file().parent.mkdir(parents=True, exist_ok=True)
    with open(config_file(), "w") as f:
        yaml.dump(Config.get_default().model_dump(), f)

# Load config
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    config_module.CONFIG = Config()

# Now import models
from bagels.models.database.db import Base
from bagels.models.account import Account
from bagels.models.category import Category
from bagels.models.record import Record
from bagels.models.split import Split


# ---------- CLI Runner Fixture ---------- #


@pytest.fixture(scope="function")
def cli_runner():
    """
    Provide Click CliRunner for CLI command testing.

    Returns:
        CliRunner: Click testing utility for invoking CLI commands
    """
    return CliRunner()


# ---------- Sample Database with Records ---------- #


@pytest.fixture(scope="function")
def sample_db_with_records():
    """
    Create in-memory database with comprehensive test data.

    Creates:
    - 5 sample accounts (Savings, Checking, Credit Card, Investment, Cash)
    - 10 sample categories with hierarchy
    - 30 sample records spanning 3 months (2026-01, 2026-02, 2026-03)
    - Both income and expense records
    - Records with splits

    Returns:
        Session: SQLAlchemy session with populated test data
    """
    # Create in-memory SQLite engine
    engine = create_engine("sqlite:///:memory:")

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create sample accounts
    accounts = [
        Account(
            name="Savings",
            description="Emergency fund and savings",
            beginningBalance=5000.0,
            repaymentDate=None,
            hidden=False,
        ),
        Account(
            name="Checking",
            description="Primary checking account",
            beginningBalance=2000.0,
            repaymentDate=None,
            hidden=False,
        ),
        Account(
            name="Credit Card",
            description="Visa credit card",
            beginningBalance=-1500.0,
            repaymentDate=None,
            hidden=False,
        ),
        Account(
            name="Investment",
            description="Stock portfolio",
            beginningBalance=10000.0,
            repaymentDate=None,
            hidden=False,
        ),
        Account(
            name="Cash",
            description="Physical cash on hand",
            beginningBalance=200.0,
            repaymentDate=None,
            hidden=False,
        ),
    ]

    for account in accounts:
        session.add(account)
    session.flush()

    # Create sample categories with hierarchy
    from bagels.models.category import Nature

    categories = [
        # Top level categories
        Category(
            name="Food", parentCategoryId=None, nature=Nature.NEED, color="#FF5733"
        ),
        Category(
            name="Transport", parentCategoryId=None, nature=Nature.NEED, color="#33FF57"
        ),
        Category(
            name="Housing", parentCategoryId=None, nature=Nature.NEED, color="#3357FF"
        ),
        Category(
            name="Entertainment",
            parentCategoryId=None,
            nature=Nature.WANT,
            color="#F033FF",
        ),
        Category(
            name="Healthcare",
            parentCategoryId=None,
            nature=Nature.NEED,
            color="#FF33F0",
        ),
    ]

    for category in categories:
        session.add(category)
    session.flush()

    # Create subcategories
    food_groceries = Category(
        name="Groceries",
        parentCategoryId=categories[0].id,
        nature=Nature.NEED,
        color="#FF5733",
    )
    food_restaurants = Category(
        name="Restaurants",
        parentCategoryId=categories[0].id,
        nature=Nature.WANT,
        color="#FF8C33",
    )
    transport_gas = Category(
        name="Gas",
        parentCategoryId=categories[1].id,
        nature=Nature.NEED,
        color="#33FF57",
    )
    transport_public = Category(
        name="Public Transit",
        parentCategoryId=categories[1].id,
        nature=Nature.NEED,
        color="#57FF33",
    )
    entertainment_movies = Category(
        name="Movies",
        parentCategoryId=categories[3].id,
        nature=Nature.WANT,
        color="#F033FF",
    )
    entertainment_games = Category(
        name="Games",
        parentCategoryId=categories[3].id,
        nature=Nature.WANT,
        color="#FF33A8",
    )

    subcategories = [
        food_groceries,
        food_restaurants,
        transport_gas,
        transport_public,
        entertainment_movies,
        entertainment_games,
    ]

    for category in subcategories:
        session.add(category)
    session.flush()

    # Create sample records spanning 3 months
    base_dates = [
        datetime(2026, 1, 15),  # January
        datetime(2026, 2, 15),  # February
        datetime(2026, 3, 15),  # March
    ]

    records_data = [
        # January records
        {
            "label": "Grocery Shopping",
            "amount": 150.50,
            "category": food_groceries.id,
            "account": accounts[1].id,
            "date": base_dates[0],
            "is_income": False,
        },
        {
            "label": "Gas Station",
            "amount": 45.00,
            "category": transport_gas.id,
            "account": accounts[2].id,
            "date": base_dates[0] + timedelta(days=2),
            "is_income": False,
        },
        {
            "label": "Rent Payment",
            "amount": 1500.00,
            "category": categories[2].id,
            "account": accounts[1].id,
            "date": base_dates[0] + timedelta(days=5),
            "is_income": False,
        },
        {
            "label": "Salary",
            "amount": 3500.00,
            "category": None,
            "account": accounts[1].id,
            "date": base_dates[0] + timedelta(days=7),
            "is_income": True,
        },
        {
            "label": "Restaurant Dinner",
            "amount": 65.00,
            "category": food_restaurants.id,
            "account": accounts[2].id,
            "date": base_dates[0] + timedelta(days=10),
            "is_income": False,
        },
        {
            "label": "Movie Tickets",
            "amount": 25.00,
            "category": entertainment_movies.id,
            "account": accounts[1].id,
            "date": base_dates[0] + timedelta(days=12),
            "is_income": False,
        },
        {
            "label": "Public Transit Pass",
            "amount": 80.00,
            "category": transport_public.id,
            "account": accounts[1].id,
            "date": base_dates[0] + timedelta(days=15),
            "is_income": False,
        },
        {
            "label": "Doctor Visit",
            "amount": 120.00,
            "category": categories[4].id,
            "account": accounts[1].id,
            "date": base_dates[0] + timedelta(days=18),
            "is_income": False,
        },
        {
            "label": "Groceries",
            "amount": 180.25,
            "category": food_groceries.id,
            "account": accounts[1].id,
            "date": base_dates[0] + timedelta(days=20),
            "is_income": False,
        },
        {
            "label": "Gas",
            "amount": 42.50,
            "category": transport_gas.id,
            "account": accounts[2].id,
            "date": base_dates[0] + timedelta(days=22),
            "is_income": False,
        },
        # February records
        {
            "label": "Grocery Shopping",
            "amount": 165.00,
            "category": food_groceries.id,
            "account": accounts[1].id,
            "date": base_dates[1],
            "is_income": False,
        },
        {
            "label": "Gas Station",
            "amount": 38.75,
            "category": transport_gas.id,
            "account": accounts[2].id,
            "date": base_dates[1] + timedelta(days=2),
            "is_income": False,
        },
        {
            "label": "Rent Payment",
            "amount": 1500.00,
            "category": categories[2].id,
            "account": accounts[1].id,
            "date": base_dates[1] + timedelta(days=5),
            "is_income": False,
        },
        {
            "label": "Salary",
            "amount": 3500.00,
            "category": None,
            "account": accounts[1].id,
            "date": base_dates[1] + timedelta(days=7),
            "is_income": True,
        },
        {
            "label": "Restaurant Lunch",
            "amount": 35.50,
            "category": food_restaurants.id,
            "account": accounts[2].id,
            "date": base_dates[1] + timedelta(days=10),
            "is_income": False,
        },
        {
            "label": "Video Game",
            "amount": 59.99,
            "category": entertainment_games.id,
            "account": accounts[2].id,
            "date": base_dates[1] + timedelta(days=12),
            "is_income": False,
        },
        {
            "label": "Public Transit Pass",
            "amount": 80.00,
            "category": transport_public.id,
            "account": accounts[1].id,
            "date": base_dates[1] + timedelta(days=15),
            "is_income": False,
        },
        {
            "label": "Pharmacy",
            "amount": 45.00,
            "category": categories[4].id,
            "account": accounts[1].id,
            "date": base_dates[1] + timedelta(days=18),
            "is_income": False,
        },
        {
            "label": "Groceries",
            "amount": 175.50,
            "category": food_groceries.id,
            "account": accounts[1].id,
            "date": base_dates[1] + timedelta(days=20),
            "is_income": False,
        },
        {
            "label": "Gas",
            "amount": 40.00,
            "category": transport_gas.id,
            "account": accounts[2].id,
            "date": base_dates[1] + timedelta(days=22),
            "is_income": False,
        },
        # March records
        {
            "label": "Grocery Shopping",
            "amount": 155.75,
            "category": food_groceries.id,
            "account": accounts[1].id,
            "date": base_dates[2],
            "is_income": False,
        },
        {
            "label": "Gas Station",
            "amount": 48.25,
            "category": transport_gas.id,
            "account": accounts[2].id,
            "date": base_dates[2] + timedelta(days=2),
            "is_income": False,
        },
        {
            "label": "Rent Payment",
            "amount": 1500.00,
            "category": categories[2].id,
            "account": accounts[1].id,
            "date": base_dates[2] + timedelta(days=5),
            "is_income": False,
        },
        {
            "label": "Salary",
            "amount": 3500.00,
            "category": None,
            "account": accounts[1].id,
            "date": base_dates[2] + timedelta(days=7),
            "is_income": True,
        },
        {
            "label": "Restaurant Dinner",
            "amount": 72.00,
            "category": food_restaurants.id,
            "account": accounts[2].id,
            "date": base_dates[2] + timedelta(days=10),
            "is_income": False,
        },
        {
            "label": "Movie Tickets",
            "amount": 28.00,
            "category": entertainment_movies.id,
            "account": accounts[1].id,
            "date": base_dates[2] + timedelta(days=12),
            "is_income": False,
        },
        {
            "label": "Public Transit Pass",
            "amount": 80.00,
            "category": transport_public.id,
            "account": accounts[1].id,
            "date": base_dates[2] + timedelta(days=15),
            "is_income": False,
        },
        {
            "label": "Dentist",
            "amount": 150.00,
            "category": categories[4].id,
            "account": accounts[1].id,
            "date": base_dates[2] + timedelta(days=18),
            "is_income": False,
        },
        {
            "label": "Groceries",
            "amount": 190.00,
            "category": food_groceries.id,
            "account": accounts[1].id,
            "date": base_dates[2] + timedelta(days=20),
            "is_income": False,
        },
        {
            "label": "Gas",
            "amount": 44.50,
            "category": transport_gas.id,
            "account": accounts[2].id,
            "date": base_dates[2] + timedelta(days=22),
            "is_income": False,
        },
    ]

    records = []
    for record_data in records_data:
        record = Record(
            label=record_data["label"],
            amount=record_data["amount"],
            date=record_data["date"],
            accountId=record_data["account"],
            categoryId=record_data["category"],
            isIncome=record_data["is_income"],
            isTransfer=False,
        )
        session.add(record)
        records.append(record)

    # Add some records with splits
    record_with_split = Record(
        label="Shopping with Split",
        amount=200.00,
        date=base_dates[2] + timedelta(days=1),
        accountId=accounts[1].id,
        categoryId=food_groceries.id,
        isIncome=False,
        isTransfer=False,
    )
    session.add(record_with_split)
    session.flush()

    # Create splits for the record
    split1 = Split(
        recordId=record_with_split.id, categoryId=food_groceries.id, amount=150.00
    )
    split2 = Split(
        recordId=record_with_split.id, categoryId=entertainment_games.id, amount=50.00
    )
    session.add(split1)
    session.add(split2)

    session.commit()

    yield session

    # Clean up
    session.close()
    Base.metadata.drop_all(engine)


# ---------- Sample Data Fixtures ---------- #


@pytest.fixture(scope="function")
def sample_accounts(sample_db_with_records):
    """
    Return list of Account objects from sample DB.

    Returns:
        list: List of 5 Account objects
    """
    return sample_db_with_records.query(Account).all()


@pytest.fixture(scope="function")
def sample_categories(sample_db_with_records):
    """
    Return list of Category objects from sample DB.

    Returns:
        list: List of Category objects (16 total: 5 top level + 6 subcategories)
    """
    return sample_db_with_records.query(Category).all()


@pytest.fixture(scope="function")
def sample_records(sample_db_with_records):
    """
    Return list of Record objects from sample DB.

    Returns:
        list: List of Record objects (31 total)
    """
    return sample_db_with_records.query(Record).all()


# ---------- Session Fixture ---------- #


@pytest.fixture(scope="function")
def cli_session(sample_db_with_records):
    """
    Provide session for CLI test queries.

    Returns:
        Session: SQLAlchemy session from sample_db_with_records
    """
    return sample_db_with_records
