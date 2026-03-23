"""Tests for SQLite-only startup and legacy sync deprecation warning."""

import inspect

import yaml

import bagels.config as config_mod
import bagels.locations as locations_mod
from bagels.app import App
from bagels.config import Config, load_config
from bagels.locations import config_file, set_custom_root


def test_app_startup_has_no_sync_worker():
    assert not hasattr(App, "run_startup_import")

    on_mount_source = inspect.getsource(App.on_mount)
    assert "run_startup_import" not in on_mount_source

    module_source = inspect.getsource(__import__("bagels.app", fromlist=["*"]))
    assert "pull_from_remote" not in module_source
    assert "run_full_import" not in module_source


def test_load_config_warns_once_for_legacy_sync_settings(tmp_path, capsys):
    original_root = locations_mod._custom_root
    original_config = config_mod.CONFIG

    set_custom_root(tmp_path)
    try:
        cfg = Config.get_default().model_dump()
        cfg["git"]["enabled"] = True
        cfg["state"]["sync_deprecation_warned"] = False

        cfg_path = config_file()
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cfg_path, "w", encoding="utf-8") as handle:
            yaml.safe_dump(cfg, handle)

        config_mod.CONFIG = None
        load_config()
        first = capsys.readouterr()
        assert "Git and YAML sync features were removed" in first.out

        with open(cfg_path, "r", encoding="utf-8") as handle:
            persisted = yaml.safe_load(handle)
        assert persisted["state"]["sync_deprecation_warned"] is True

        load_config()
        second = capsys.readouterr()
        assert "Git and YAML sync features were removed" not in second.out
    finally:
        config_mod.CONFIG = original_config
        set_custom_root(original_root)
