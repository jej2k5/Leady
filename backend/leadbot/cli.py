"""Typer-powered command-line interface for leadbot."""

from __future__ import annotations

import csv
import io
from pathlib import Path

import typer

from . import __version__
from .db.queries import list_companies
from .db.session import get_connection
from .exports.csv_export import OUTREACH_QUEUE_HEADERS, build_outreach_queue_csv, build_raw_candidates_csv
from .exports.google_sheets import append_rows_to_google_sheets

app = typer.Typer(help="Leady backend CLI")


@app.command()
def version() -> None:
    """Print package version."""
    typer.echo(__version__)


@app.command("export-csv")
def export_csv(
    output: Path = typer.Option(..., "--output", "-o", help="Output CSV path"),
    run_id: int | None = typer.Option(None, "--run-id", help="Filter rows by run id"),
    export_type: str = typer.Option("outreach", "--type", help="outreach or raw"),
    include_unknown_stage: bool = typer.Option(False, help="Include rows with unknown stage in outreach"),
) -> None:
    """Export outreach_queue.csv or raw_candidates.csv via CLI."""
    with get_connection() as conn:
        companies = list_companies(conn, run_id=run_id)

    if export_type == "outreach":
        content = build_outreach_queue_csv(companies, include_unknown_stage=include_unknown_stage)
    elif export_type == "raw":
        content = build_raw_candidates_csv(companies)
    else:
        raise typer.BadParameter("--type must be 'outreach' or 'raw'")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    typer.echo(str(output))


@app.command("export-google-sheets")
def export_google_sheets(
    run_id: int | None = typer.Option(None, "--run-id", help="Filter rows by run id"),
) -> None:
    """Send outreach queue export to Google Sheets when ENABLE_GOOGLE_SHEETS=true."""
    with get_connection() as conn:
        companies = list_companies(conn, run_id=run_id)

    content = build_outreach_queue_csv(companies)
    reader = csv.DictReader(io.StringIO(content))
    headers = reader.fieldnames or OUTREACH_QUEUE_HEADERS
    rows = [[row.get(header, "") for header in headers] for row in reader]
    result = append_rows_to_google_sheets(headers, rows)
    typer.echo(str(result))


def main(argv: list[str] | None = None) -> int:
    """Entry point used by `python -m leadbot` and tests."""
    try:
        app(args=argv, standalone_mode=False)
    except SystemExit as exc:
        return int(exc.code)
    return 0
