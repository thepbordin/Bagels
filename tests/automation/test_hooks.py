"""Reduction-focused tests for manager CRUD sync behavior.

Phase 5 removed background YAML/Git sync hooks from manager modules.
These tests ensure the legacy hook code paths are absent while CRUD still works.
"""

from datetime import datetime
import inspect

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import bagels.managers.accounts as accounts_mod
import bagels.managers.categories as categories_mod
import bagels.managers.persons as persons_mod
import bagels.managers.record_templates as templates_mod
import bagels.managers.records as records_mod
from bagels.models.category import Nature
from bagels.models.database.db import Base

MANAGER_MODULES = [
    accounts_mod,
    categories_mod,
    persons_mod,
    templates_mod,
    records_mod,
]


@pytest.fixture()
def isolated_manager_db():
    """Bind manager Session factories to a clean in-memory database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    originals = {module: module.Session for module in MANAGER_MODULES}
    for module in MANAGER_MODULES:
        module.Session = session_factory

    try:
        yield
    finally:
        for module, original in originals.items():
            module.Session = original
        Base.metadata.drop_all(engine)


@pytest.mark.parametrize("module", MANAGER_MODULES, ids=lambda module: module.__name__)
def test_manager_modules_have_no_background_sync_hooks(module):
    source = inspect.getsource(module)

    assert "_trigger_entity_export" not in source
    assert "_trigger_export_and_commit" not in source
    assert "threading.Thread(" not in source


def test_record_crud_still_works_without_sync_hooks(isolated_manager_db):
    account = accounts_mod.create_account(
        {"name": "Primary", "beginningBalance": 100.0, "hidden": False}
    )
    category = categories_mod.create_category(
        {"name": "Groceries", "nature": Nature.NEED, "color": "#00AA00"}
    )

    created = records_mod.create_record(
        {
            "label": "Coffee",
            "amount": 4.5,
            "date": datetime(2026, 3, 21),
            "accountId": account.id,
            "categoryId": category.id,
            "isIncome": False,
            "isTransfer": False,
        }
    )

    assert created.id is not None

    updated = records_mod.update_record(created.id, {"label": "Coffee Beans"})
    assert updated is not None
    assert updated.label == "Coffee Beans"

    deleted = records_mod.delete_record(created.id)
    assert deleted is not None
    assert deleted.id == created.id
