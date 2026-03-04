"""Typer-powered command-line interface for leadbot."""

from __future__ import annotations

import typer

from . import __version__

app = typer.Typer(help="Leady backend CLI")


@app.command()
def version() -> None:
    """Print package version."""
    typer.echo(__version__)


def main(argv: list[str] | None = None) -> int:
    """Entry point used by `python -m leadbot` and tests."""
    try:
        app(args=argv, standalone_mode=False)
    except SystemExit as exc:
        return int(exc.code)
    return 0
