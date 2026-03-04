"""Tests for CLI behavior."""

from pathlib import Path

from leadbot.cli import main


def test_cli_version(capsys) -> None:
    assert main(["version"]) == 0
    output = capsys.readouterr().out.strip()
    assert output


def test_cli_run_and_stats(capsys) -> None:
    assert main(["run", "--days", "7", "--sources", "funding,hiring", "--include-unknown-stage"]) == 0
    run_output = capsys.readouterr().out
    assert "run complete" in run_output

    assert main(["stats"]) == 0
    stats_output = capsys.readouterr().out
    assert "runs=" in stats_output


def test_cli_create_user_and_export(tmp_path: Path, capsys) -> None:
    assert main(["create-user", "--email", "cli@example.com", "--full-name", "CLI User"]) == 0
    user_output = capsys.readouterr().out
    assert "created user" in user_output

    output_file = tmp_path / "outreach.csv"
    assert main(["export", "--output", str(output_file), "--include-unknown-stage"]) == 0
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8").startswith("rank,company_name")
