"""Shared fixtures for tests/integration/."""

import pytest
import yaml
import warnings
import tempfile
import shutil
import os
import uuid
from click.testing import CliRunner
from datetime import datetime, timedelta
from pathlib import Path
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
from bagels.models.category import Category, Nature
from bagels.models.record import Record

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
    """Click CliRunner instance for invoking CLI commands."""
    return CliRunner()


@pytest.fixture
def sample_cli_db():
    """File-based DB in a unique temp dir with accounts, categories, and records.

    Each test using this fixture gets its OWN isolated temp directory and database.
    No sharing between tests - prevents UNIQUE constraint failures.

    Creates:
    - 1 account (Test Bank, beginningBalance=1000)
    - 1 category (Food)
    - 5 expense records dated 2026-03-01 through 2026-03-05
    """
    # Create a unique temp directory for this test
    tmpdir = tempfile.mkdtemp(prefix=f"bagels_test_{uuid.uuid4().hex}_")

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

    session = TestSession()

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

    # Clean up: close session first
    session.close()

    # Dispose of the engine to release file handles
    test_engine.dispose()

    # Remove the temp directory explicitly
    # Note: We do NOT reset custom root to None here because:
    # 1. Each test using this fixture gets its own unique temp dir
    # 2. The next test will set its own custom root anyway
    # 3. Resetting to None can break tests that expect a custom root to be set
    if Path(tmpdir).exists():
        shutil.rmtree(tmpdir, ignore_errors=True)
