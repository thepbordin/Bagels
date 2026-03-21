"""Regression tests for custom-root database session rebinding."""

from bagels.locations import set_custom_root
import bagels.locations as locations_mod
from bagels.models.database.app import init_db
import bagels.managers.accounts as accounts_mod


def test_init_db_rebinds_preloaded_manager_sessions_for_custom_root(tmp_path):
    original_root = locations_mod._custom_root

    set_custom_root(tmp_path)
    try:
        init_db()

        bind_url = str(accounts_mod.Session.kw["bind"].url)
        assert str((tmp_path / "db.db").resolve()) in bind_url

        # Should query successfully against the rebound database.
        assert accounts_mod.get_accounts_count(get_hidden=True) >= 1
    finally:
        set_custom_root(original_root)
        init_db()
