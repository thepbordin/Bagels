"""Integration tests for Phase 5 SQLite-only CRUD behavior."""

from datetime import datetime
import warnings
from unittest.mock import patch

import pytest
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bagels.config import Config, config_file
import bagels.config as config_module
import bagels.locations as locations_mod
from bagels.locations import database_file, set_custom_root
from bagels.models.database.app import init_db
from bagels.models.database.db import Base
import bagels.models.database.app as app_mod
import bagels.managers.accounts as accounts_mod
import bagels.managers.categories as categories_mod
import bagels.managers.persons as persons_mod
import bagels.managers.record_templates as templates_mod
import bagels.managers.records as records_mod
from bagels.models.category import Nature

# Ensure ORM relationships are registered.
from bagels.models import split  # noqa: F401

if not config_file().exists():
    config_file().parent.mkdir(parents=True, exist_ok=True)
    with open(config_file(), "w", encoding="utf-8") as handle:
        yaml.safe_dump(Config.get_default().model_dump(), handle)


@pytest.fixture()
def sqlite_only_runtime(tmp_path):
    original_root = locations_mod._custom_root
    original_engine = app_mod.db_engine
    original_config = config_module.CONFIG
    original_sessions = {
        app_mod: app_mod.Session,
        accounts_mod: accounts_mod.Session,
        categories_mod: categories_mod.Session,
        persons_mod: persons_mod.Session,
        templates_mod: templates_mod.Session,
        records_mod: records_mod.Session,
    }

    set_custom_root(tmp_path)
    engine = create_engine(f"sqlite:///{database_file().resolve()}")
    Base.metadata.create_all(engine)

    app_mod.db_engine = engine
    for module in original_sessions:
        setattr(module, "Session", sessionmaker(bind=engine))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        config_module.CONFIG = Config()

    init_db()

    try:
        yield tmp_path
    finally:
        for module, session_factory in original_sessions.items():
            setattr(module, "Session", session_factory)
        app_mod.db_engine = original_engine
        config_module.CONFIG = original_config
        set_custom_root(original_root)


def test_crud_operations_do_not_write_yaml_files(sqlite_only_runtime):
    root = sqlite_only_runtime

    account = accounts_mod.create_account(
        {"name": "Integration Bank", "beginningBalance": 1200.0, "hidden": False}
    )
    category = categories_mod.create_category(
        {"name": "Food", "nature": Nature.NEED, "color": "#123456"}
    )
    person = persons_mod.create_person({"name": "Alice"})

    templates_mod.create_template(
        {
            "label": "Lunch Template",
            "amount": 10.0,
            "accountId": account.id,
            "categoryId": category.id,
            "isIncome": False,
        }
    )

    record = records_mod.create_record(
        {
            "label": "Lunch",
            "amount": 12.5,
            "date": datetime(2026, 3, 21),
            "accountId": account.id,
            "categoryId": category.id,
            "personId": person.id,
            "isIncome": False,
            "isTransfer": False,
        }
    )
    records_mod.update_record(record.id, {"label": "Lunch Updated"})
    records_mod.delete_record(record.id)

    assert not (root / "accounts.yaml").exists()
    assert not (root / "categories.yaml").exists()
    assert not (root / "persons.yaml").exists()
    assert not (root / "templates.yaml").exists()
    assert not (root / "records").exists()


def test_crud_never_calls_git_auto_commit(sqlite_only_runtime):
    account = accounts_mod.create_account(
        {"name": "No Git", "beginningBalance": 50.0, "hidden": False}
    )

    with patch("bagels.git.operations.auto_commit_yaml") as commit_mock:
        accounts_mod.update_account(account.id, {"name": "Still No Git"})
        accounts_mod.delete_account(account.id)

    commit_mock.assert_not_called()
