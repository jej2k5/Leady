"""Tests for the initial CLI behavior."""

from leadbot.cli import main


def test_cli_version(capsys) -> None:
    assert main(["--version"]) == 0
    output = capsys.readouterr().out.strip()
    assert output
