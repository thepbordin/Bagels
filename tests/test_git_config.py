"""
Tests for GitConfig Pydantic model and its integration with the Config model.

Covers requirements CFG-01 through CFG-05.
"""

import pytest
import yaml
from pathlib import Path

from bagels.config import Config, GitConfig


class TestGitConfigDefaults:
    """Test 1: GitConfig() defaults."""

    def test_defaults(self):
        cfg = GitConfig()
        assert cfg.enabled is False
        assert cfg.auto_commit is True
        assert cfg.auto_push is False
        assert cfg.auto_pull is False
        assert cfg.remote == "origin"
        assert cfg.branch == "main"
        assert cfg.commit_message_format is None


class TestConfigHasGitField:
    """Test 2: Config() has a `git` attribute of type GitConfig."""

    def test_config_git_field_type(self):
        cfg = Config.get_default()
        assert hasattr(cfg, "git")
        assert isinstance(cfg.git, GitConfig)


class TestGitConfigCustomValues:
    """Test 3: GitConfig can be constructed with custom values."""

    def test_custom_values(self):
        cfg = GitConfig(enabled=True, auto_push=True)
        assert cfg.enabled is True
        assert cfg.auto_push is True
        # other defaults unchanged
        assert cfg.auto_commit is True
        assert cfg.auto_pull is False


class TestCommitMessageFormat:
    """Test 4: commit_message_format field accepts None and a str value."""

    def test_none_value(self):
        cfg = GitConfig()
        assert cfg.commit_message_format is None

    def test_string_value(self):
        cfg = GitConfig(commit_message_format="chore: auto-commit {filename}")
        assert cfg.commit_message_format == "chore: auto-commit {filename}"


class TestGitConfigPersistedToYaml:
    """Test 5: GitConfig.enabled=False is written to config YAML via ensure_yaml_fields."""

    def test_git_in_yaml(self, tmp_path, monkeypatch):
        config_path = tmp_path / "config.yaml"
        monkeypatch.setattr("bagels.locations._custom_root", tmp_path)

        cfg = Config()
        cfg.ensure_yaml_fields()

        with open(config_path) as f:
            data = yaml.safe_load(f)

        assert "git" in data
        assert data["git"]["enabled"] is False
