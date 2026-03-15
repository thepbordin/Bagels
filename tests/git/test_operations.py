"""
Tests for git operations module.

Covers requirements GIT-02, GIT-07.
"""

import threading
import pytest
from pathlib import Path


class TestAutoCommitYaml:
    """Tests 6-8: auto_commit_yaml behavior."""

    def test_dirty_file_returns_true_and_creates_commit(
        self, tmp_git_repo, monkeypatch
    ):
        """Test 6: auto_commit_yaml with a dirty file returns True and creates a commit."""
        repo, data_dir = tmp_git_repo
        monkeypatch.setattr("bagels.locations._custom_root", data_dir)

        # Import after monkeypatching so data_directory() returns our tmp dir
        from bagels.git.operations import auto_commit_yaml

        yaml_file = data_dir / "records" / "2026-03.yaml"
        yaml_file.write_text("records: []\n")

        result = auto_commit_yaml(yaml_file, "test: add records file")

        assert result is True
        commits = list(repo.iter_commits())
        assert len(commits) >= 1
        assert "test: add records file" in commits[0].message

    def test_clean_index_returns_true_no_new_commit(self, tmp_git_repo, monkeypatch):
        """Test 7: auto_commit_yaml with clean index returns True but makes no new commit."""
        repo, data_dir = tmp_git_repo
        monkeypatch.setattr("bagels.locations._custom_root", data_dir)

        from bagels.git.operations import auto_commit_yaml

        yaml_file = data_dir / "records" / "2026-03.yaml"
        yaml_file.write_text("records: []\n")

        # First commit to make index clean for this file
        repo.index.add([str(yaml_file.relative_to(data_dir))])
        repo.index.commit("initial commit")

        commit_count_before = len(list(repo.iter_commits()))
        result = auto_commit_yaml(yaml_file, "test: no changes")

        assert result is True
        commit_count_after = len(list(repo.iter_commits()))
        assert commit_count_after == commit_count_before

    def test_no_git_repo_returns_false_no_raise(self, tmp_path, monkeypatch):
        """Test 8: auto_commit_yaml when no git repo exists returns False without raising."""
        monkeypatch.setattr("bagels.locations._custom_root", tmp_path)

        from bagels.git.operations import auto_commit_yaml

        yaml_file = tmp_path / "records" / "2026-03.yaml"
        yaml_file.parent.mkdir(exist_ok=True)
        yaml_file.write_text("records: []\n")

        result = auto_commit_yaml(yaml_file, "test: no repo")
        assert result is False


class TestGetStatus:
    """Test 9: get_status returns list of changed/untracked file paths."""

    def test_returns_untracked_files(self, tmp_git_repo, monkeypatch):
        repo, data_dir = tmp_git_repo
        monkeypatch.setattr("bagels.locations._custom_root", data_dir)

        from bagels.git.operations import get_status

        yaml_file = data_dir / "records" / "2026-03.yaml"
        yaml_file.write_text("records: []\n")

        status = get_status()
        assert isinstance(status, list)
        assert any("2026-03.yaml" in path for path in status)

    def test_no_repo_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr("bagels.locations._custom_root", tmp_path)

        from bagels.git.operations import get_status

        status = get_status()
        assert status == []


class TestGetLog:
    """Tests 10-11: get_log behavior."""

    def test_returns_list_of_dicts(self, tmp_git_repo, monkeypatch):
        """Test 10: get_log returns list of dicts with keys hash, message, date, author."""
        repo, data_dir = tmp_git_repo
        monkeypatch.setattr("bagels.locations._custom_root", data_dir)

        from bagels.git.operations import get_log

        yaml_file = data_dir / "records" / "2026-03.yaml"
        yaml_file.write_text("records: []\n")
        repo.index.add([str(yaml_file.relative_to(data_dir))])
        repo.index.commit("test commit")

        log = get_log()
        assert isinstance(log, list)
        assert len(log) >= 1
        entry = log[0]
        assert "hash" in entry
        assert "message" in entry
        assert "date" in entry
        assert "author" in entry

    def test_no_repo_returns_empty_list(self, tmp_path, monkeypatch):
        """Test 11: get_log returns empty list when no git repo exists."""
        monkeypatch.setattr("bagels.locations._custom_root", tmp_path)

        from bagels.git.operations import get_log

        log = get_log()
        assert log == []


class TestGitLock:
    """Test 12: _GIT_LOCK is a threading.Lock() at module level in operations.py."""

    def test_git_lock_is_threading_lock(self):
        from bagels.git import operations

        assert hasattr(operations, "_GIT_LOCK")
        assert isinstance(operations._GIT_LOCK, type(threading.Lock()))
