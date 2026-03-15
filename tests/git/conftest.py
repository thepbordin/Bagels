"""
Conftest for tests/git/ — provides the tmp_git_repo fixture.
"""

import pytest
from git import Repo


@pytest.fixture
def tmp_git_repo(tmp_path):
    """Initialize a git repo at tmp_path, create records/ dir, yield (repo, tmp_path)."""
    repo = Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    records_dir = tmp_path / "records"
    records_dir.mkdir()
    yield repo, tmp_path
