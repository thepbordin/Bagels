"""
Deprecated Git operations module.

Git sync support was removed as part of SQLite-only runtime reduction.
All functions are preserved as no-op compatibility shims.
"""

from pathlib import Path


def auto_commit_yaml(filepath: Path, message: str) -> bool:
    """Compatibility shim: Git sync removed."""
    _ = filepath, message
    return False


def push_to_remote(remote_name: str = "origin", branch: str = "main") -> bool:
    """Compatibility shim: Git sync removed."""
    _ = remote_name, branch
    return False


def pull_from_remote(
    remote_name: str = "origin", branch: str = "main", silent: bool = False
) -> bool:
    """Compatibility shim: Git sync removed."""
    _ = remote_name, branch, silent
    return False


def get_status() -> list[str]:
    """Compatibility shim: Git sync removed."""
    return []


def get_log(max_count: int = 10) -> list[dict]:
    """Compatibility shim: Git sync removed."""
    _ = max_count
    return []
