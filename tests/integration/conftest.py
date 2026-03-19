"""Shared fixtures for tests/integration/."""

import pytest
import yaml
import warnings
from click.testing import CliRunner
from datetime import datetime, timedelta
from tempfile import TemporaryDirectory

from bagels.config import Config, config_file
import bagels.config as config_module

# Create config file if needed before importing models
if not config_file().exists():
    config_file().parent.mkdir(parents=True, exist_ok=True)
    with open(config_file(), "w") as f:
        yaml.dump(Config.get_default().model_dump(), f)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    config_module.CONFIG = Config()

from bagels.locations import set_custom_root
from bagels.models.database.app import init_db, Session
from bagels.models.account import Account
from bagels.models.category import Category, Nature
from bagels.models.record import Record

# Import all models to ensure relationships are properly configured
from bagels.models import split  # noqa: F401


@pytest.fixture
def cli_runner():
    """Click CliRunner instance for invoking CLI commands."""
    return CliRunner()


@pytest.fixture
def sample_cli_db():
    """File-based DB in a temp dir with accounts, categories, and records.

    Creates:
    - 1 account (Test Bank, beginningBalance=1000)
    - 1 category (Food)
    - 5 expense records dated 2026-03-01 through 2026-03-05
    """
    with TemporaryDirectory() as tmpdir:
        set_custom_root(tmpdir)
        init_db()

        session = Session()

        account = Account(name="Test Bank", slug="test-bank", beginningBalance=1000.0)
        session.add(account)
        session.flush()

        food = Category(name="Food", slug="food", nature=Nature.NEED, color="#FF0000")
        session.add(food)
        session.flush()

        base = datetime(2026, 3, 1)
        for i in range(5):
            session.add(
                Record(
                    label=f"Test Record {i + 1}",
                    amount=10.0 * (i + 1),
                    date=base + timedelta(days=i),
                    accountId=account.id,
                    categoryId=food.id,
                    isIncome=False,
                    isTransfer=False,
                )
            )

        session.commit()

        yield session

        session.close()

    # Reset custom root after temp dir is torn down
    set_custom_root(None)
