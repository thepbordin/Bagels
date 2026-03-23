"""Tests for deprecated git compatibility shims in Phase 5."""

from pathlib import Path

from bagels.git.operations import (
    auto_commit_yaml,
    get_log,
    get_status,
    pull_from_remote,
    push_to_remote,
)
from bagels.git.repository import create_gitignore, initialize_git_repo


def test_git_operations_are_noop_shims(tmp_path):
    yaml_file = tmp_path / "records" / "2026-03.yaml"
    yaml_file.parent.mkdir(parents=True, exist_ok=True)
    yaml_file.write_text("records: []\n", encoding="utf-8")

    assert auto_commit_yaml(yaml_file, "sync: test") is False
    assert push_to_remote() is False
    assert pull_from_remote() is False
    assert get_status() == []
    assert get_log() == []


def test_git_repository_shims_are_safe_noops(tmp_path):
    data_dir = Path(tmp_path)

    assert initialize_git_repo(data_dir) is False

    # Should not raise, even though repository setup was removed.
    create_gitignore(data_dir)
