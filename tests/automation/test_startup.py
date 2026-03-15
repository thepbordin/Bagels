"""
Tests for startup YAML import worker in app.py.

Requirements: DATA-08 (startup YAML→SQLite sync), GIT-08 (auto_pull before import)

Tests confirm:
- run_startup_import calls run_full_import once
- auto_pull gating (git.enabled + git.auto_pull required)
- pull failure does not block import
- import failure is swallowed (TUI never crashes)
- on_mount schedules the worker
- CONFIG=None handled gracefully
"""

import inspect
from unittest.mock import MagicMock, call, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(*, git_enabled: bool = False, auto_pull: bool = False) -> MagicMock:
    """Return a mock CONFIG with typical git settings."""
    cfg = MagicMock()
    cfg.git.enabled = git_enabled
    cfg.git.auto_pull = auto_pull
    cfg.git.remote = "origin"
    cfg.git.branch = "main"
    return cfg


def _call_worker(app_instance: MagicMock, config_value, mock_pull, mock_import) -> None:
    """
    Call the underlying worker function directly, bypassing the Textual @work decorator.

    The decorator wraps the function; we want to invoke the raw logic. We find
    the method on the class and call it directly so tests stay fast/unit-level.
    """
    # Patch the lazy imports inside the worker
    with (
        patch("bagels.config.CONFIG", config_value),
        patch("bagels.git.operations.pull_from_remote", mock_pull),
        patch("bagels.importer.importer.run_full_import", mock_import),
    ):
        # Import here to pick up the patched module
        from bagels.app import App  # noqa: PLC0415

        instance = App.__new__(App)
        instance.app = MagicMock()
        instance.notify = MagicMock()
        # call_from_thread should execute the callback immediately in tests
        instance.app.call_from_thread = lambda fn: fn()
        # Call the unwrapped function directly
        App.run_startup_import.__wrapped__(instance)


# ---------------------------------------------------------------------------
# Test 1: run_startup_import calls run_full_import once
# ---------------------------------------------------------------------------


def test_run_startup_import_calls_run_full_import():
    """DATA-08: worker always calls run_full_import exactly once."""
    config = _make_config()
    mock_pull = MagicMock()
    mock_import = MagicMock()

    with (
        patch("bagels.config.CONFIG", config),
        patch("bagels.git.operations.pull_from_remote", mock_pull),
        patch("bagels.importer.importer.run_full_import", mock_import),
    ):
        from bagels.app import App

        instance = App.__new__(App)
        instance.app = MagicMock()
        instance.notify = MagicMock()
        instance.app.call_from_thread = lambda fn: fn()
        App.run_startup_import.__wrapped__(instance)

    mock_import.assert_called_once()


# ---------------------------------------------------------------------------
# Test 2: auto_pull=True calls pull_from_remote before run_full_import
# ---------------------------------------------------------------------------


def test_run_startup_import_auto_pull_true_calls_pull():
    """GIT-08: when git.enabled=True and git.auto_pull=True, pull is called."""
    config = _make_config(git_enabled=True, auto_pull=True)
    call_order = []
    mock_pull = MagicMock(side_effect=lambda **kw: call_order.append("pull"))
    mock_import = MagicMock(side_effect=lambda: call_order.append("import"))

    with (
        patch("bagels.config.CONFIG", config),
        patch("bagels.git.operations.pull_from_remote", mock_pull),
        patch("bagels.importer.importer.run_full_import", mock_import),
    ):
        from bagels.app import App

        instance = App.__new__(App)
        instance.app = MagicMock()
        instance.notify = MagicMock()
        instance.app.call_from_thread = lambda fn: fn()
        App.run_startup_import.__wrapped__(instance)

    mock_pull.assert_called_once()
    mock_import.assert_called_once()
    assert call_order == ["pull", "import"], "pull must run before import"


# ---------------------------------------------------------------------------
# Test 3: auto_pull=False does NOT call pull_from_remote
# ---------------------------------------------------------------------------


def test_run_startup_import_auto_pull_false_skips_pull():
    """GIT-08: git.enabled=True but git.auto_pull=False — no pull."""
    config = _make_config(git_enabled=True, auto_pull=False)
    mock_pull = MagicMock()
    mock_import = MagicMock()

    with (
        patch("bagels.config.CONFIG", config),
        patch("bagels.git.operations.pull_from_remote", mock_pull),
        patch("bagels.importer.importer.run_full_import", mock_import),
    ):
        from bagels.app import App

        instance = App.__new__(App)
        instance.app = MagicMock()
        instance.notify = MagicMock()
        instance.app.call_from_thread = lambda fn: fn()
        App.run_startup_import.__wrapped__(instance)

    mock_pull.assert_not_called()
    mock_import.assert_called_once()


# ---------------------------------------------------------------------------
# Test 4: git.enabled=False does NOT call pull_from_remote even if auto_pull=True
# ---------------------------------------------------------------------------


def test_run_startup_import_git_disabled_skips_pull():
    """GIT-08: git.enabled=False — pull never happens regardless of auto_pull."""
    config = _make_config(git_enabled=False, auto_pull=True)
    mock_pull = MagicMock()
    mock_import = MagicMock()

    with (
        patch("bagels.config.CONFIG", config),
        patch("bagels.git.operations.pull_from_remote", mock_pull),
        patch("bagels.importer.importer.run_full_import", mock_import),
    ):
        from bagels.app import App

        instance = App.__new__(App)
        instance.app = MagicMock()
        instance.notify = MagicMock()
        instance.app.call_from_thread = lambda fn: fn()
        App.run_startup_import.__wrapped__(instance)

    mock_pull.assert_not_called()
    mock_import.assert_called_once()


# ---------------------------------------------------------------------------
# Test 5: pull_from_remote raising an exception does not prevent run_full_import
# ---------------------------------------------------------------------------


def test_run_startup_import_pull_failure_does_not_block_import():
    """GIT-08: if pull raises, import still runs."""
    config = _make_config(git_enabled=True, auto_pull=True)
    mock_pull = MagicMock(side_effect=Exception("network unreachable"))
    mock_import = MagicMock()

    with (
        patch("bagels.config.CONFIG", config),
        patch("bagels.git.operations.pull_from_remote", mock_pull),
        patch("bagels.importer.importer.run_full_import", mock_import),
    ):
        from bagels.app import App

        instance = App.__new__(App)
        instance.app = MagicMock()
        instance.notify = MagicMock()
        instance.app.call_from_thread = lambda fn: fn()
        App.run_startup_import.__wrapped__(instance)

    mock_import.assert_called_once()


# ---------------------------------------------------------------------------
# Test 6: run_full_import raising an exception does not propagate
# ---------------------------------------------------------------------------


def test_run_startup_import_import_failure_is_swallowed():
    """DATA-08: exceptions from run_full_import are swallowed; TUI never crashes."""
    config = _make_config()
    mock_pull = MagicMock()
    mock_import = MagicMock(side_effect=Exception("db locked"))

    with (
        patch("bagels.config.CONFIG", config),
        patch("bagels.git.operations.pull_from_remote", mock_pull),
        patch("bagels.importer.importer.run_full_import", mock_import),
    ):
        from bagels.app import App

        instance = App.__new__(App)
        instance.app = MagicMock()
        instance.notify = MagicMock()
        instance.app.call_from_thread = lambda fn: fn()
        # Must not raise
        try:
            App.run_startup_import.__wrapped__(instance)
        except Exception as exc:
            raise AssertionError(f"Exception leaked out of worker: {exc}") from exc


# ---------------------------------------------------------------------------
# Test 7: on_mount calls self.run_startup_import()
# ---------------------------------------------------------------------------


def test_on_mount_calls_run_startup_import():
    """DATA-08: on_mount schedules the startup import worker."""
    from bagels.app import App

    assert hasattr(App, "run_startup_import"), (
        "App must have a run_startup_import method"
    )
    # Verify on_mount source code calls self.run_startup_import()
    source = inspect.getsource(App.on_mount)
    assert "run_startup_import" in source, (
        "on_mount must call self.run_startup_import()"
    )


# ---------------------------------------------------------------------------
# Test 8: CONFIG=None returns early (test environment guard)
# ---------------------------------------------------------------------------


def test_run_startup_import_none_config_returns_early():
    """DATA-08: CONFIG=None in test environments — worker returns without error."""
    mock_import = MagicMock()

    with (
        patch("bagels.config.CONFIG", None),
        patch("bagels.importer.importer.run_full_import", mock_import),
    ):
        from bagels.app import App

        instance = App.__new__(App)
        instance.app = MagicMock()
        instance.notify = MagicMock()
        instance.app.call_from_thread = lambda fn: fn()
        try:
            App.run_startup_import.__wrapped__(instance)
        except Exception as exc:
            raise AssertionError(f"Exception with CONFIG=None: {exc}") from exc

    mock_import.assert_not_called()
