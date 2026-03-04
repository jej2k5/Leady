"""Tests for CLI behavior."""

import importlib.util
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
    assert main(["create-user", "--email", "cli@example.com", "--password", "secret123", "--name", "CLI User", "--role", "admin"]) == 0
    user_output = capsys.readouterr().out
    assert "created user" in user_output

    output_file = tmp_path / "outreach.csv"
    assert main(["export", "--output", str(output_file), "--include-unknown-stage"]) == 0
    assert output_file.exists()
    assert output_file.read_text(encoding="utf-8").startswith("rank,company_name")


def test_cli_serve_requires_uvicorn(monkeypatch, capsys) -> None:
    original_find_spec = importlib.util.find_spec

    def fake_find_spec(name: str, package=None):  # type: ignore[no-untyped-def]
        if name == "uvicorn":
            return None
        return original_find_spec(name, package)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)

    assert main(["serve", "--host", "127.0.0.1", "--port", "8010"]) == 2
    error_output = capsys.readouterr().err
    assert "Missing dependency: uvicorn" in error_output
