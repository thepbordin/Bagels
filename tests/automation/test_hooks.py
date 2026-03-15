"""
Tests for auto-export hooks wired into manager CRUD operations.

These tests verify:
- create/update/delete_record spawn background daemon threads
- _trigger_export_and_commit calls export_records_for_month with correct args
- CONFIG=None guard prevents any export from firing
- git.enabled=False guard skips auto_commit_yaml
- Exceptions inside hooks do NOT propagate to callers
- Non-record manager hooks (accounts) call the correct export function
"""

import threading
from datetime import datetime
from unittest.mock import MagicMock, patch, call
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_config(*, git_enabled: bool = True, auto_commit: bool = True):
    """Return a mock CONFIG object with a .git attribute."""
    cfg = MagicMock()
    cfg.git.enabled = git_enabled
    cfg.git.auto_commit = auto_commit
    cfg.git.commit_message_format = None
    return cfg


# ---------------------------------------------------------------------------
# Tests for _trigger_export_and_commit in records manager
# ---------------------------------------------------------------------------


class TestTriggerExportAndCommit:
    """Unit tests for the _trigger_export_and_commit helper."""

    def test_returns_early_when_config_is_none(self):
        """Test 8: CONFIG=None guard returns early without calling any export."""
        import bagels.managers.records as records_mod
        import bagels.config as config_mod

        original_config = config_mod.CONFIG
        try:
            config_mod.CONFIG = None

            export_mock = MagicMock()
            with patch("bagels.export.exporter.export_records_for_month", export_mock):
                # Should not raise
                records_mod._trigger_export_and_commit(
                    datetime(2026, 3, 14), "add", "Coffee"
                )

            export_mock.assert_not_called()
        finally:
            config_mod.CONFIG = original_config

    def test_calls_export_with_correct_year_month(self, tmp_path):
        """Test 7: _trigger_export_and_commit calls export_records_for_month
        with the correct year and month extracted from the record date."""
        import bagels.managers.records as records_mod
        import bagels.config as config_mod
        from bagels.locations import set_custom_root

        original_config = config_mod.CONFIG
        set_custom_root(tmp_path)
        try:
            config_mod.CONFIG = _make_mock_config(git_enabled=False)

            with patch(
                "bagels.export.exporter.export_records_for_month"
            ) as export_mock:
                export_mock.return_value = tmp_path / "records" / "2026-05.yaml"
                records_mod._trigger_export_and_commit(
                    datetime(2026, 5, 20), "update", "Rent"
                )

            export_mock.assert_called_once()
            _, kwargs_or_args = export_mock.call_args[0], export_mock.call_args
            args = export_mock.call_args[0]
            # args: (session, output_dir, year, month)
            assert args[2] == 2026
            assert args[3] == 5
        finally:
            config_mod.CONFIG = original_config
            set_custom_root(None)

    def test_skips_auto_commit_when_git_disabled(self, tmp_path):
        """Test 9: git.enabled=False calls export but skips auto_commit_yaml."""
        import bagels.managers.records as records_mod
        import bagels.config as config_mod
        from bagels.locations import set_custom_root

        original_config = config_mod.CONFIG
        set_custom_root(tmp_path)
        try:
            config_mod.CONFIG = _make_mock_config(git_enabled=False)

            with (
                patch("bagels.export.exporter.export_records_for_month") as export_mock,
                patch("bagels.git.operations.auto_commit_yaml") as commit_mock,
            ):
                export_mock.return_value = tmp_path / "records" / "2026-03.yaml"
                records_mod._trigger_export_and_commit(
                    datetime(2026, 3, 1), "delete", "Test"
                )

            export_mock.assert_called_once()
            commit_mock.assert_not_called()
        finally:
            config_mod.CONFIG = original_config
            set_custom_root(None)

    def test_exception_does_not_propagate(self, tmp_path):
        """Test 10: Exception inside _trigger_export_and_commit is swallowed."""
        import bagels.managers.records as records_mod
        import bagels.config as config_mod
        from bagels.locations import set_custom_root

        original_config = config_mod.CONFIG
        set_custom_root(tmp_path)
        try:
            config_mod.CONFIG = _make_mock_config(git_enabled=False)

            with patch(
                "bagels.export.exporter.export_records_for_month",
                side_effect=RuntimeError("disk full"),
            ):
                # Must not raise
                records_mod._trigger_export_and_commit(
                    datetime(2026, 3, 1), "add", "Boom"
                )
        finally:
            config_mod.CONFIG = original_config
            set_custom_root(None)


# ---------------------------------------------------------------------------
# Tests for background threading in records CRUD
# ---------------------------------------------------------------------------


class TestRecordHooksSpawnThread:
    """Verify create/update/delete_record spawn daemon background threads."""

    def _mock_db_session_factory(self):
        """Return a mock session factory that yields a session which returns a
        fake Record on .add/.commit."""
        fake_record = MagicMock()
        fake_record.id = 1
        fake_record.date = datetime(2026, 3, 14)
        fake_record.label = "Coffee"

        session = MagicMock()
        session.query.return_value.get.return_value = fake_record
        # make session.__enter__/__exit__ work if used as context manager
        session.__enter__ = MagicMock(return_value=session)
        session.__exit__ = MagicMock(return_value=False)

        return session, fake_record

    @patch("bagels.managers.records.threading")
    def test_create_record_spawns_background_thread(self, mock_threading):
        """Test 4: create_record spawns a background thread."""
        mock_thread = MagicMock()
        mock_threading.Thread.return_value = mock_thread

        import bagels.managers.records as records_mod

        fake_record = MagicMock()
        fake_record.date = datetime(2026, 3, 14)
        fake_record.label = "Coffee"

        # Patch the entire session lifecycle to avoid DB access
        with patch.object(records_mod, "Session") as MockSession:
            mock_session = MagicMock()
            mock_session.__enter__ = MagicMock(return_value=mock_session)
            mock_session.__exit__ = MagicMock(return_value=False)
            MockSession.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = (
                None
            )

            # create_record uses Session() directly (not as context manager)
            mock_session.refresh.side_effect = lambda obj: None
            mock_session.expunge.side_effect = lambda obj: None

            # Patch Record constructor to return fake_record
            with patch("bagels.managers.records.Record", return_value=fake_record):
                try:
                    records_mod.create_record(
                        {
                            "label": "Coffee",
                            "amount": 5.0,
                            "date": datetime(2026, 3, 14),
                        }
                    )
                except Exception:
                    pass  # DB may fail; we only check thread spawning

        mock_threading.Thread.assert_called()
        call_kwargs = mock_threading.Thread.call_args[1]
        assert call_kwargs.get("target") == records_mod._trigger_export_and_commit
        assert call_kwargs.get("daemon") is True
        mock_thread.start.assert_called_once()

    @patch("bagels.managers.records.threading")
    def test_update_record_spawns_background_thread(self, mock_threading):
        """Test 5: update_record spawns a background thread."""
        mock_thread = MagicMock()
        mock_threading.Thread.return_value = mock_thread

        import bagels.managers.records as records_mod

        fake_record = MagicMock()
        fake_record.date = datetime(2026, 3, 10)
        fake_record.label = "Lunch"

        with patch.object(records_mod, "Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value = mock_session
            mock_session.query.return_value.get.return_value = fake_record

            try:
                records_mod.update_record(1, {"label": "Lunch updated"})
            except Exception:
                pass

        mock_threading.Thread.assert_called()
        call_kwargs = mock_threading.Thread.call_args[1]
        assert call_kwargs.get("target") == records_mod._trigger_export_and_commit
        assert call_kwargs.get("daemon") is True
        mock_thread.start.assert_called_once()

    @patch("bagels.managers.records.threading")
    def test_delete_record_spawns_background_thread(self, mock_threading):
        """Test 6: delete_record spawns a background thread with captured date."""
        mock_thread = MagicMock()
        mock_threading.Thread.return_value = mock_thread

        import bagels.managers.records as records_mod

        fake_record = MagicMock()
        fake_record.date = datetime(2026, 3, 5)
        fake_record.label = "Uber"

        with patch.object(records_mod, "Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value = mock_session
            mock_session.query.return_value.get.return_value = fake_record

            try:
                records_mod.delete_record(1)
            except Exception:
                pass

        mock_threading.Thread.assert_called()
        call_kwargs = mock_threading.Thread.call_args[1]
        assert call_kwargs.get("target") == records_mod._trigger_export_and_commit
        assert call_kwargs.get("daemon") is True
        mock_thread.start.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for non-record manager hooks (accounts)
# ---------------------------------------------------------------------------


class TestAccountHookSpawnsThread:
    """Test 11: create_account hook calls export_accounts in background thread."""

    @patch("bagels.managers.accounts.threading")
    def test_create_account_spawns_export_thread(self, mock_threading):
        """create_account should spawn a daemon background thread."""
        mock_thread = MagicMock()
        mock_threading.Thread.return_value = mock_thread

        import bagels.managers.accounts as accounts_mod

        fake_account = MagicMock()
        fake_account.id = 1

        with patch.object(accounts_mod, "Session") as MockSession:
            mock_session = MagicMock()
            MockSession.return_value = mock_session

            with patch("bagels.managers.accounts.Account", return_value=fake_account):
                try:
                    accounts_mod.create_account(
                        {"name": "Savings", "beginningBalance": 0.0}
                    )
                except Exception:
                    pass

        mock_threading.Thread.assert_called()
        call_kwargs = mock_threading.Thread.call_args[1]
        assert call_kwargs.get("daemon") is True
        mock_thread.start.assert_called_once()
