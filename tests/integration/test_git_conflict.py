"""Reduced conflict-marker tests for import compatibility utilities."""

import warnings

import pytest
import yaml

from bagels.config import Config, config_file
import bagels.config as config_module
import bagels.locations as locations_mod
from bagels.importer.importer import (
    ConflictError,
    check_for_conflict_markers,
    run_full_import,
)
from bagels.locations import set_custom_root
from bagels.models.database.app import init_db

CONFLICT_TEXT = """\
<<<<<<< HEAD
accounts:
  acc_a:
    name: Device A
=======
accounts:
  acc_a:
    name: Device B
>>>>>>> feature
"""


if not config_file().exists():
    config_file().parent.mkdir(parents=True, exist_ok=True)
    with open(config_file(), "w", encoding="utf-8") as handle:
        yaml.safe_dump(Config.get_default().model_dump(), handle)


@pytest.fixture()
def isolated_root(tmp_path):
    original_root = locations_mod._custom_root
    original_config = config_module.CONFIG

    set_custom_root(tmp_path)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        config_module.CONFIG = Config()

    init_db()

    try:
        yield tmp_path
    finally:
        config_module.CONFIG = original_config
        set_custom_root(original_root)


def test_conflict_marker_scan_detects_root_and_records_files(isolated_root):
    root = isolated_root
    (root / "accounts.yaml").write_text(CONFLICT_TEXT, encoding="utf-8")
    records_dir = root / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    (records_dir / "2026-03.yaml").write_text(CONFLICT_TEXT, encoding="utf-8")

    conflicts = check_for_conflict_markers(root)

    assert conflicts == ["accounts.yaml", "records/2026-03.yaml"]


def test_run_full_import_fails_fast_when_conflict_markers_exist(isolated_root):
    root = isolated_root
    (root / "accounts.yaml").write_text(CONFLICT_TEXT, encoding="utf-8")

    with pytest.raises(ConflictError) as exc_info:
        run_full_import()

    assert "accounts.yaml" in str(exc_info.value)


def test_conflict_marker_scan_returns_empty_for_clean_yaml(isolated_root):
    root = isolated_root
    (root / "accounts.yaml").write_text(
        "accounts:\n  acc_clean:\n    name: Clean\n", encoding="utf-8"
    )

    assert check_for_conflict_markers(root) == []
