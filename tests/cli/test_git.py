"""
Integration tests for bagels git CLI command group.

Tests GIT-03, GIT-04, GIT-05, GIT-06 requirements:
- bagels git status: reports uncommitted YAML changes
- bagels git log: prints recent commit history
- bagels git sync: commits dirty files and pushes
- bagels git pull: export -> commit -> pull -> reimport sequence
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
from click.testing import CliRunner


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_runner() -> CliRunner:
    return CliRunner(mix_stderr=False)


# ---------------------------------------------------------------------------
# Test 1: bagels git status — dirty repo prints file paths
# ---------------------------------------------------------------------------


def test_git_status_dirty_repo():
    """GIT-03: status with dirty repo prints file paths."""
    runner = _make_runner()

    with patch(
        "bagels.git.operations.get_status",
        return_value=["records/2026-03.yaml", "accounts.yaml"],
    ):
        from bagels.cli.git import git

        result = runner.invoke(git, ["status"])

    assert result.exit_code == 0
    assert "records/2026-03.yaml" in result.output
    assert "accounts.yaml" in result.output


# ---------------------------------------------------------------------------
# Test 2: bagels git status — clean repo prints "Working tree clean"
# ---------------------------------------------------------------------------


def test_git_status_clean_repo():
    """GIT-03: status with clean repo prints clean message."""
    runner = _make_runner()

    with patch("bagels.git.operations.get_status", return_value=[]):
        from bagels.cli.git import git

        result = runner.invoke(git, ["status"])

    assert result.exit_code == 0
    assert "clean" in result.output.lower()


# ---------------------------------------------------------------------------
# Test 3: bagels git status — no git repo prints appropriate message
# ---------------------------------------------------------------------------


def test_git_status_no_repo():
    """GIT-03: status with no git repo exits 0 with appropriate message."""
    runner = _make_runner()

    # get_status returns [] when no repo (by design in operations.py)
    with patch("bagels.git.operations.get_status", return_value=[]):
        from bagels.cli.git import git

        result = runner.invoke(git, ["status"])

    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# Test 4: bagels git log — with commits prints hash + message
# ---------------------------------------------------------------------------


def test_git_log_with_commits():
    """GIT-04: log with commits prints hash and message lines."""
    runner = _make_runner()

    fake_log = [
        {
            "hash": "abc1234",
            "message": "sync: records/2026-03.yaml",
            "date": "2026-03-15T10:00:00+00:00",
            "author": "Alice",
        },
        {
            "hash": "def5678",
            "message": "sync: accounts.yaml",
            "date": "2026-03-14T09:00:00+00:00",
            "author": "Alice",
        },
    ]

    with patch("bagels.git.operations.get_log", return_value=fake_log):
        from bagels.cli.git import git

        result = runner.invoke(git, ["log"])

    assert result.exit_code == 0
    assert "abc1234" in result.output
    assert "sync: records/2026-03.yaml" in result.output
    assert "def5678" in result.output


# ---------------------------------------------------------------------------
# Test 5: bagels git log — no commits / no repo prints "No commits"
# ---------------------------------------------------------------------------


def test_git_log_no_commits():
    """GIT-04: log with no commits or no repo prints empty/no-commits message."""
    runner = _make_runner()

    with patch("bagels.git.operations.get_log", return_value=[]):
        from bagels.cli.git import git

        result = runner.invoke(git, ["log"])

    assert result.exit_code == 0
    assert "no commits" in result.output.lower()


# ---------------------------------------------------------------------------
# Test 6: bagels git sync — calls auto_commit_yaml for each dirty file then push
# ---------------------------------------------------------------------------


def test_git_sync_calls_commit_and_push():
    """GIT-05: sync calls auto_commit_yaml for each dirty file then push_to_remote."""
    runner = _make_runner()

    dirty_files = ["records/2026-03.yaml", "accounts.yaml"]

    mock_config = MagicMock()
    mock_config.git.remote = "origin"
    mock_config.git.branch = "main"

    with (
        patch("bagels.git.operations.get_status", return_value=dirty_files),
        patch(
            "bagels.git.operations.auto_commit_yaml", return_value=True
        ) as mock_commit,
        patch("bagels.git.operations.push_to_remote", return_value=True) as mock_push,
        patch("bagels.models.database.app.init_db"),
        patch("bagels.config.load_config"),
        patch("bagels.config.CONFIG", mock_config),
        patch("bagels.locations.data_directory", return_value=Path("/fake/data")),
    ):
        from bagels.cli.git import git

        result = runner.invoke(git, ["sync"])

    assert result.exit_code == 0
    # auto_commit_yaml called once per dirty file
    assert mock_commit.call_count == len(dirty_files)
    # push_to_remote called once
    mock_push.assert_called_once_with("origin", "main")


# ---------------------------------------------------------------------------
# Test 7: bagels git sync — push failure prints warning but exits 0
# ---------------------------------------------------------------------------


def test_git_sync_push_failure_exits_zero():
    """GIT-05: sync when push fails prints warning but exits 0 (non-blocking)."""
    runner = _make_runner()

    mock_config = MagicMock()
    mock_config.git.remote = "origin"
    mock_config.git.branch = "main"

    with (
        patch(
            "bagels.git.operations.get_status", return_value=["records/2026-03.yaml"]
        ),
        patch("bagels.git.operations.auto_commit_yaml", return_value=True),
        patch("bagels.git.operations.push_to_remote", return_value=False),
        patch("bagels.models.database.app.init_db"),
        patch("bagels.config.load_config"),
        patch("bagels.config.CONFIG", mock_config),
        patch("bagels.locations.data_directory", return_value=Path("/fake/data")),
    ):
        from bagels.cli.git import git

        result = runner.invoke(git, ["sync"])

    assert result.exit_code == 0
    # Should mention push failure as a warning
    assert (
        "warn" in result.output.lower()
        or "failed" in result.output.lower()
        or "push" in result.output.lower()
    )


# ---------------------------------------------------------------------------
# Test 8: bagels git pull — sequence: export -> commit -> pull -> reimport
# ---------------------------------------------------------------------------


def test_git_pull_sequence():
    """GIT-06: pull follows export -> commit -> pull -> reimport order."""
    runner = _make_runner()

    call_order = []

    mock_config = MagicMock()
    mock_config.git.remote = "origin"
    mock_config.git.branch = "main"

    def mock_export(*args, **kwargs):
        call_order.append("export")
        return MagicMock()

    def mock_commit(*args, **kwargs):
        call_order.append("commit")
        return True

    def mock_pull(*args, **kwargs):
        call_order.append("pull")
        return True

    def mock_reimport(*args, **kwargs):
        call_order.append("reimport")

    with (
        patch("bagels.models.database.app.init_db"),
        patch("bagels.config.load_config"),
        patch("bagels.config.CONFIG", mock_config),
        patch("bagels.locations.data_directory", return_value=Path("/fake/data")),
        # Export functions
        patch("bagels.export.exporter.export_accounts", side_effect=mock_export),
        patch("bagels.export.exporter.export_categories", side_effect=mock_export),
        patch("bagels.export.exporter.export_persons", side_effect=mock_export),
        patch("bagels.export.exporter.export_templates", side_effect=mock_export),
        patch(
            "bagels.export.exporter.export_records_by_month", side_effect=mock_export
        ),
        patch("bagels.models.database.app.Session", return_value=MagicMock()),
        # Git operations
        patch(
            "bagels.git.operations.get_status", return_value=["records/2026-03.yaml"]
        ),
        patch("bagels.git.operations.auto_commit_yaml", side_effect=mock_commit),
        patch("bagels.git.operations.pull_from_remote", side_effect=mock_pull),
        # Reimport
        patch("bagels.cli.git._run_full_import", side_effect=mock_reimport),
    ):
        from bagels.cli.git import git

        result = runner.invoke(git, ["pull"])

    assert result.exit_code == 0
    # export must come before pull
    assert call_order.index("export") < call_order.index("pull")
    # pull must come before reimport
    assert call_order.index("pull") < call_order.index("reimport")


# ---------------------------------------------------------------------------
# Test 9: bagels git pull — pull failure prints error and exits non-zero
# ---------------------------------------------------------------------------


def test_git_pull_failure_exits_nonzero():
    """GIT-06: pull when remote pull fails prints error and exits non-zero."""
    runner = _make_runner()

    mock_config = MagicMock()
    mock_config.git.remote = "origin"
    mock_config.git.branch = "main"

    with (
        patch("bagels.models.database.app.init_db"),
        patch("bagels.config.load_config"),
        patch("bagels.config.CONFIG", mock_config),
        patch("bagels.locations.data_directory", return_value=Path("/fake/data")),
        patch("bagels.export.exporter.export_accounts", return_value=MagicMock()),
        patch("bagels.export.exporter.export_categories", return_value=MagicMock()),
        patch("bagels.export.exporter.export_persons", return_value=MagicMock()),
        patch("bagels.export.exporter.export_templates", return_value=MagicMock()),
        patch(
            "bagels.export.exporter.export_records_by_month", return_value=MagicMock()
        ),
        patch("bagels.models.database.app.Session", return_value=MagicMock()),
        patch("bagels.git.operations.get_status", return_value=[]),
        patch("bagels.git.operations.pull_from_remote", return_value=False),
    ):
        from bagels.cli.git import git

        result = runner.invoke(git, ["pull"])

    assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Test 10: bagels git (no subcommand) prints help listing all subcommands
# ---------------------------------------------------------------------------


def test_git_group_help_lists_subcommands():
    """GIT-03..06: 'bagels git' with no subcommand shows help with all four subcommands."""
    runner = _make_runner()

    from bagels.cli.git import git

    result = runner.invoke(git, [])

    assert result.exit_code == 0
    assert "sync" in result.output
    assert "pull" in result.output
    assert "status" in result.output
    assert "log" in result.output
