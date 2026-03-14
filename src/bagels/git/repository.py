"""
Git repository management functions.

Provides utilities for initializing Git repositories in the Bagels data directory
and creating appropriate .gitignore files to exclude SQLite database files.
"""

from git import Repo, InvalidGitRepositoryError
from pathlib import Path


def initialize_git_repo(data_dir: Path) -> bool:
    """Initialize Git repository in data directory.

    Args:
        data_dir: Path to data directory

    Returns:
        bool: True if newly created, False if already exists
    """
    try:
        # Check if already initialized
        Repo(data_dir)
        return False  # Already exists
    except InvalidGitRepositoryError:
        # Initialize new repository
        Repo.init(data_dir)
        return True  # Newly created


def create_gitignore(data_dir: Path) -> None:
    """Create .gitignore for data directory.

    Creates a .gitignore file in the data directory that excludes
    SQLite database files and temporary files from Git tracking.

    Args:
        data_dir: Path to data directory
    """
    gitignore_path = data_dir / '.gitignore'
    gitignore_content = """# Bagels ignore patterns
*.db
*.db-shm
*.db-wal
*.tmp
backups/
"""
    with open(gitignore_path, 'w') as f:
        f.write(gitignore_content.strip())
