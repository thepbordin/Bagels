"""Tests for deprecated git CLI compatibility module."""

from click.testing import CliRunner

from bagels.cli.git import git


def test_deprecated_git_group_is_not_a_functional_command_set():
    runner = CliRunner()
    result = runner.invoke(git, [])

    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_deprecated_git_subcommand_is_unavailable():
    runner = CliRunner()
    result = runner.invoke(git, ["status"])

    assert result.exit_code != 0
    assert "No such command 'status'" in result.output
