"""
Deprecated Git compatibility package.

Git/YAML sync was removed as part of SQLite-only runtime reduction.
"""

from bagels.git.repository import initialize_git_repo, create_gitignore

__all__ = ["initialize_git_repo", "create_gitignore"]
