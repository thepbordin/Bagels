"""
Integration tests for Phase 3 auto-export hooks.

Tests call manager CRUD functions against a real file-based database in a temp
directory — no mocks — and verify that actual YAML files are written to disk.

Covers:
- All 5 entity types: accounts, categories, persons, templates, records
- create / update / delete operations for accounts and records
- Monthly YAML grouping for records (records/YYYY-MM.yaml)
- Non-blocking guarantee: git failure never fails CRUD
"""

import time
import yaml
import warnings
import pytest
from datetime import datetime
from pathlib import Path

from bagels.config import Config, config_file
import bagels.config as config_module

# Ensure CONFIG is set before any model / manager imports
if not config_file().exists():
    config_file().parent.mkdir(parents=True, exist_ok=True)
    with open(config_file(), "w") as f:
        yaml.dump(Config.get_default().model_dump(), f)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    if config_module.CONFIG is None:
        config_module.CONFIG = Config()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bagels.locations import set_custom_root, database_file
from bagels.models.database.app import init_db
from bagels.models.database.db import Base
import bagels.models.database.app as app_mod
import bagels.managers.accounts as accounts_mod
import bagels.managers.categories as categories_mod
import bagels.managers.persons as persons_mod
import bagels.managers.record_templates as templates_mod
import bagels.managers.records as records_mod

# Ensure all ORM relationships are wired up
from bagels.models import split  # noqa: F401


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def db_with_temp_root(tmp_path):
    """
    Function-scoped fixture that:
    1. Points all app paths at tmp_path (via set_custom_root)
    2. Creates a fresh SQLite DB at tmp_path/db.db
    3. Rebinds db_engine and every manager Session to the new DB
    4. Sets up a real Config instance so export hooks fire
    5. Yields tmp_path as the data root
    6. Tears down: resets engine, sessions, and custom root
    """
    # Step 1 — redirect all paths
    set_custom_root(tmp_path)

    # Step 2 — create a fresh engine pointing at the temp DB
    temp_db_path = database_file()  # now resolves inside tmp_path
    new_engine = create_engine(f"sqlite:///{temp_db_path.resolve()}")
    Base.metadata.create_all(new_engine)

    # Step 3 — patch the global engine and Sessions
    original_engine = app_mod.db_engine
    app_mod.db_engine = new_engine

    original_sessions = {}
    for mod, name in [
        (app_mod, "Session"),
        (accounts_mod, "Session"),
        (categories_mod, "Session"),
        (persons_mod, "Session"),
        (templates_mod, "Session"),
        (records_mod, "Session"),
    ]:
        original_sessions[(id(mod), name)] = getattr(mod, name)
        new_session_factory = sessionmaker(bind=new_engine)
        setattr(mod, name, new_session_factory)

    # Step 4 — initialise default data (outside-source account, default categories)
    init_db()

    # Step 5 — ensure CONFIG is live
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        config_module.CONFIG = Config()

    yield tmp_path

    # Teardown — restore everything
    for mod, name in [
        (app_mod, "Session"),
        (accounts_mod, "Session"),
        (categories_mod, "Session"),
        (persons_mod, "Session"),
        (templates_mod, "Session"),
        (records_mod, "Session"),
    ]:
        setattr(mod, name, original_sessions[(id(mod), name)])

    app_mod.db_engine = original_engine
    set_custom_root(None)


# ---------------------------------------------------------------------------
# Account tests
# ---------------------------------------------------------------------------


def test_create_account_writes_yaml(db_with_temp_root):
    """create_account triggers daemon thread that writes accounts.yaml to disk."""
    from bagels.managers.accounts import create_account

    create_account(
        {"name": "Integration Bank", "beginningBalance": 999.0, "hidden": False}
    )
    time.sleep(0.5)

    yaml_path = db_with_temp_root / "accounts.yaml"
    assert yaml_path.exists(), "accounts.yaml was not written after create_account()"

    with open(yaml_path) as f:
        raw = yaml.safe_load(f)

    # YAML structure: {"accounts": {"acc_1": {name: ..., ...}, ...}}
    data = raw.get("accounts", raw) if isinstance(raw, dict) else raw
    assert data, "accounts.yaml is empty"
    names = [v.get("name") for v in data.values() if isinstance(v, dict)]
    assert "Integration Bank" in names, (
        f"'Integration Bank' not found in accounts.yaml. Names: {names}"
    )


def test_update_account_writes_yaml(db_with_temp_root):
    """update_account triggers export; accounts.yaml reflects updated name."""
    from bagels.managers.accounts import create_account, update_account

    account = create_account(
        {"name": "To Update", "beginningBalance": 100.0, "hidden": False}
    )
    time.sleep(0.5)

    update_account(account.id, {"name": "Updated Name"})
    time.sleep(0.5)

    yaml_path = db_with_temp_root / "accounts.yaml"
    assert yaml_path.exists(), "accounts.yaml not found after update_account()"

    with open(yaml_path) as f:
        raw = yaml.safe_load(f)

    data = raw.get("accounts", raw) if isinstance(raw, dict) else raw
    names = [v.get("name") for v in data.values() if isinstance(v, dict)]
    assert "Updated Name" in names, (
        f"'Updated Name' not found in accounts.yaml after update. Names: {names}"
    )


def test_delete_account_writes_yaml(db_with_temp_root):
    """delete_account triggers export; deleted account slug absent from accounts.yaml."""
    from bagels.managers.accounts import create_account, delete_account

    account = create_account(
        {"name": "To Delete", "beginningBalance": 0.0, "hidden": False}
    )
    time.sleep(0.5)

    # Capture the slug before deletion
    yaml_path = db_with_temp_root / "accounts.yaml"
    with open(yaml_path) as f:
        raw = yaml.safe_load(f)
    pre_data = raw.get("accounts", raw) if isinstance(raw, dict) else raw

    # Find slug for "To Delete"
    deleted_slug = None
    for slug, v in pre_data.items():
        if isinstance(v, dict) and v.get("name") == "To Delete":
            deleted_slug = slug
            break
    assert deleted_slug is not None, "'To Delete' account not found pre-deletion"

    delete_account(account.id)
    time.sleep(0.5)

    with open(yaml_path) as f:
        raw = yaml.safe_load(f)
    post_data = raw.get("accounts", raw) if isinstance(raw, dict) else raw

    assert deleted_slug not in post_data, (
        f"Deleted account slug '{deleted_slug}' still present in accounts.yaml after deletion"
    )


# ---------------------------------------------------------------------------
# Category test
# ---------------------------------------------------------------------------


def test_create_category_writes_yaml(db_with_temp_root):
    """create_category triggers export; categories.yaml exists and contains the new category."""
    from bagels.managers.categories import create_category
    from bagels.models.category import Nature

    create_category(
        {"name": "Integration Cat", "nature": Nature.NEED, "color": "#123456"}
    )
    time.sleep(0.5)

    yaml_path = db_with_temp_root / "categories.yaml"
    assert yaml_path.exists(), "categories.yaml was not written after create_category()"

    with open(yaml_path) as f:
        raw = yaml.safe_load(f)

    # YAML structure: {"categories": {"cat_1": {name: ..., ...}, ...}}
    data = raw.get("categories", raw) if isinstance(raw, dict) else raw
    assert data, "categories.yaml is empty"
    names = [v.get("name") for v in data.values() if isinstance(v, dict)]
    assert "Integration Cat" in names, (
        f"'Integration Cat' not found in categories.yaml. Names: {names}"
    )


# ---------------------------------------------------------------------------
# Person test
# ---------------------------------------------------------------------------


def test_create_person_writes_yaml(db_with_temp_root):
    """create_person triggers export; persons.yaml exists and contains the new person."""
    from bagels.managers.persons import create_person

    create_person({"name": "Integration Person"})
    time.sleep(0.5)

    yaml_path = db_with_temp_root / "persons.yaml"
    assert yaml_path.exists(), "persons.yaml was not written after create_person()"

    with open(yaml_path) as f:
        raw = yaml.safe_load(f)

    # YAML structure: {"persons": {"person_1": {name: ..., ...}, ...}}
    data = raw.get("persons", raw) if isinstance(raw, dict) else raw
    assert data, "persons.yaml is empty"
    names = [v.get("name") for v in data.values() if isinstance(v, dict)]
    assert "Integration Person" in names, (
        f"'Integration Person' not found in persons.yaml. Names: {names}"
    )


# ---------------------------------------------------------------------------
# Template test
# ---------------------------------------------------------------------------


def test_create_template_writes_yaml(db_with_temp_root):
    """create_template triggers export; templates.yaml exists on disk."""
    from bagels.managers.accounts import create_account
    from bagels.managers.record_templates import create_template

    account = create_account(
        {"name": "Rent Account", "beginningBalance": 0.0, "hidden": False}
    )
    time.sleep(0.5)

    create_template(
        {
            "label": "Monthly Rent",
            "amount": 1200.0,
            "accountId": account.id,
            "isIncome": False,
        }
    )
    time.sleep(0.5)

    yaml_path = db_with_temp_root / "templates.yaml"
    assert yaml_path.exists(), "templates.yaml was not written after create_template()"

    with open(yaml_path) as f:
        raw = yaml.safe_load(f)

    # YAML structure: {"templates": {...}}
    data = raw.get("templates", raw) if isinstance(raw, dict) else raw
    assert data, "templates.yaml is empty"


# ---------------------------------------------------------------------------
# Record tests
# ---------------------------------------------------------------------------


def _setup_account_and_category():
    """Helper: create an account and category, return (account, category)."""
    from bagels.managers.accounts import create_account
    from bagels.managers.categories import create_category
    from bagels.models.category import Nature

    account = create_account(
        {"name": "Record Test Bank", "beginningBalance": 500.0, "hidden": False}
    )
    category = create_category(
        {"name": "Record Test Cat", "nature": Nature.WANT, "color": "#ABCDEF"}
    )
    time.sleep(0.5)
    return account, category


def test_create_record_writes_monthly_yaml(db_with_temp_root):
    """create_record writes records/2026-03.yaml with at least one record entry."""
    from bagels.managers.records import create_record

    account, category = _setup_account_and_category()

    create_record(
        {
            "label": "Coffee Integration",
            "amount": 3.50,
            "date": datetime(2026, 3, 14),
            "accountId": account.id,
            "categoryId": category.id,
            "isIncome": False,
            "isTransfer": False,
        }
    )
    time.sleep(0.5)

    yaml_path = db_with_temp_root / "records" / "2026-03.yaml"
    assert yaml_path.exists(), (
        "records/2026-03.yaml was not written after create_record()"
    )

    with open(yaml_path) as f:
        raw = yaml.safe_load(f)

    # YAML structure: {"records": {"r_2026-03-14_001": {...}, ...}}
    data = raw.get("records", raw) if isinstance(raw, dict) else raw
    assert data, "records/2026-03.yaml is empty"
    assert len(data) >= 1, "Expected at least one record entry in records/2026-03.yaml"


def test_update_record_writes_yaml(db_with_temp_root):
    """update_record re-exports 2026-03.yaml with the updated label."""
    from bagels.managers.records import create_record, update_record

    account, category = _setup_account_and_category()

    record = create_record(
        {
            "label": "Coffee Original",
            "amount": 4.00,
            "date": datetime(2026, 3, 10),
            "accountId": account.id,
            "categoryId": category.id,
            "isIncome": False,
            "isTransfer": False,
        }
    )
    time.sleep(0.5)

    update_record(record.id, {"label": "Updated Coffee"})
    time.sleep(0.5)

    yaml_path = db_with_temp_root / "records" / "2026-03.yaml"
    assert yaml_path.exists(), "records/2026-03.yaml not found after update_record()"

    with open(yaml_path) as f:
        raw = yaml.safe_load(f)

    data = raw.get("records", raw) if isinstance(raw, dict) else raw
    labels = [v.get("label") for v in data.values() if isinstance(v, dict)]
    assert "Updated Coffee" in labels, (
        f"'Updated Coffee' not found in records/2026-03.yaml after update. Labels: {labels}"
    )


def test_delete_record_writes_yaml(db_with_temp_root):
    """delete_record re-exports 2026-03.yaml; deleted record slug absent from keys."""
    from bagels.managers.records import create_record, delete_record

    account, category = _setup_account_and_category()

    record = create_record(
        {
            "label": "Delete Me",
            "amount": 5.00,
            "date": datetime(2026, 3, 5),
            "accountId": account.id,
            "categoryId": category.id,
            "isIncome": False,
            "isTransfer": False,
        }
    )
    time.sleep(0.5)

    # Capture the record slug from the exported YAML
    yaml_path = db_with_temp_root / "records" / "2026-03.yaml"
    assert yaml_path.exists(), "records/2026-03.yaml not found before delete_record()"

    with open(yaml_path) as f:
        raw = yaml.safe_load(f)
    pre_data = raw.get("records", raw) if isinstance(raw, dict) else raw

    deleted_slug = None
    for slug, v in pre_data.items():
        if isinstance(v, dict) and v.get("label") == "Delete Me":
            deleted_slug = slug
            break
    assert deleted_slug is not None, "'Delete Me' record not found pre-deletion"

    delete_record(record.id)
    time.sleep(0.5)

    with open(yaml_path) as f:
        raw = yaml.safe_load(f)
    post_data = raw.get("records", raw) if isinstance(raw, dict) else raw

    assert deleted_slug not in post_data, (
        f"Deleted record slug '{deleted_slug}' still present in records/2026-03.yaml"
    )


# ---------------------------------------------------------------------------
# Non-blocking guarantee
# ---------------------------------------------------------------------------


def test_crud_succeeds_when_git_fails(db_with_temp_root):
    """
    CRUD succeeds and accounts.yaml is written even when git auto-commit
    is enabled but no git repo exists in tmp_path/data — verifying the
    non-blocking guarantee from Phase 3.
    """
    from bagels.managers.accounts import create_account

    original_git_enabled = config_module.CONFIG.git.enabled
    original_auto_commit = config_module.CONFIG.git.auto_commit

    try:
        config_module.CONFIG.git.enabled = True
        config_module.CONFIG.git.auto_commit = True

        # No git repo in tmp_path — auto_commit_yaml will silently return False
        account = create_account(
            {"name": "Git Fail Test", "beginningBalance": 0.0, "hidden": False}
        )

        # CRUD must succeed — no exception should have been raised
        assert account is not None, "create_account() returned None — CRUD failed"
        assert account.id is not None

        time.sleep(0.5)

        yaml_path = db_with_temp_root / "accounts.yaml"
        assert yaml_path.exists(), (
            "accounts.yaml not written even though git commit silently failed — "
            "export should still run regardless of git"
        )

    finally:
        config_module.CONFIG.git.enabled = original_git_enabled
        config_module.CONFIG.git.auto_commit = original_auto_commit
