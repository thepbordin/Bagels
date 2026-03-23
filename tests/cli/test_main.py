"""Top-level CLI command routing tests."""

import pytest
from click.testing import CliRunner

from bagels.__main__ import cli


@pytest.mark.parametrize("removed_command", ["git", "export", "import"])
def test_removed_sync_commands_are_unknown(removed_command):
    runner = CliRunner()
    result = runner.invoke(cli, [removed_command])

    assert result.exit_code != 0
    assert "No such command" in result.output
    assert removed_command in result.output


def test_help_does_not_list_removed_sync_commands():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert " git " not in result.output
    assert " export " not in result.output
    assert " import " not in result.output
