"""
Git operations module for Bagels.

Provides auto_commit_yaml, push_to_remote, pull_from_remote, get_status,
and get_log helpers. All index-write operations are serialized via a
module-level threading.Lock to prevent concurrent index mutations.
"""

import threading
from pathlib import Path

from git import InvalidGitRepositoryError, Repo

from bagels.locations import data_directory

_GIT_LOCK = threading.Lock()


def _get_repo() -> Repo | None:
    """Open and return the git repo at data_directory(), or None if not a git repo."""
    try:
        return Repo(data_directory())
    except InvalidGitRepositoryError:
        return None


def auto_commit_yaml(filepath: Path, message: str) -> bool:
    """Stage and commit a YAML file to the git repository.

    Args:
        filepath: Absolute path to the YAML file to commit.
        message: Commit message.

    Returns:
        True if the operation succeeded (including when there is nothing to commit),
        False if no git repository exists. Never raises.
    """
    with _GIT_LOCK:
        try:
            repo = _get_repo()
            if repo is None:
                return False

            relative_path = filepath.relative_to(data_directory())
            repo.index.add([str(relative_path)])

            if not repo.is_dirty(index=True):
                return True

            repo.index.commit(message)
            return True
        except Exception:
            return False


def push_to_remote(remote_name: str = "origin", branch: str = "main") -> bool:
    """Push the current branch to the specified remote.

    Args:
        remote_name: Name of the git remote. Defaults to "origin".
        branch: Branch to push. Defaults to "main".

    Returns:
        True if push succeeded, False otherwise.
    """
    with _GIT_LOCK:
        try:
            repo = _get_repo()
            if repo is None:
                return False

            remote = repo.remote(remote_name)
            remote.push(branch)
            return True
        except Exception:
            return False


def pull_from_remote(
    remote_name: str = "origin", branch: str = "main", silent: bool = False
) -> bool:
    """Pull from the specified remote into the current branch.

    Args:
        remote_name: Name of the git remote. Defaults to "origin".
        branch: Branch to pull. Defaults to "main".
        silent: If True, suppress any output from git. Defaults to False.

    Returns:
        True if pull succeeded, False otherwise.
    """
    with _GIT_LOCK:
        try:
            repo = _get_repo()
            if repo is None:
                return False

            remote = repo.remote(remote_name)
            remote.pull(branch)
            return True
        except Exception:
            return False


def get_status() -> list[str]:
    """Return a list of changed and untracked file paths in the data directory.

    Returns:
        List of relative file path strings. Empty list if no git repo exists.
    """
    try:
        repo = _get_repo()
        if repo is None:
            return []

        changed = [item.a_path for item in repo.index.diff(None)]
        untracked = list(repo.untracked_files)
        return changed + untracked
    except Exception:
        return []


def get_log(max_count: int = 10) -> list[dict]:
    """Return a list of recent commit log entries.

    Args:
        max_count: Maximum number of commits to return. Defaults to 10.

    Returns:
        List of dicts with keys: hash, message, date, author.
        Empty list if no git repo exists or no commits.
    """
    try:
        repo = _get_repo()
        if repo is None:
            return []

        result = []
        for commit in repo.iter_commits(max_count=max_count):
            result.append(
                {
                    "hash": commit.hexsha[:7],
                    "message": commit.message.strip(),
                    "date": commit.committed_datetime.isoformat(),
                    "author": str(commit.author),
                }
            )
        return result
    except Exception:
        return []
