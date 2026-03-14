"""
Git repository management for Bagels data directory.

Provides functions to initialize Git repository and create .gitignore
for YAML-based data tracking.
"""

from bagels.git.repository import initialize_git_repo, create_gitignore

__all__ = ["initialize_git_repo", "create_gitignore"]
