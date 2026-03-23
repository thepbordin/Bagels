"""
Deprecated Git repository module.

Git repository initialization was removed as part of SQLite-only runtime
reduction.
"""

from pathlib import Path


def initialize_git_repo(data_dir: Path) -> bool:
    """Compatibility shim: Git repository setup removed."""
    _ = data_dir
    return False


def create_gitignore(data_dir: Path) -> None:
    """Compatibility shim: Git repository setup removed."""
    _ = data_dir
