"""Typer-powered command-line interface for leadbot."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime, timedelta
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from . import __version__
from .api.app import app as api_app
from .config import get_settings
from .db.models import Company, RawCandidate, RunStatus, SourceType, User
from .db.queries import (
    create_run,
    create_user,
    list_companies,
    list_runs,
    persist_raw_candidate,
    update_run_status,
    upsert_company,
)
from .db.session import get_connection
from .enrichment.pipeline import enrich_candidate
from .exports.csv_export import (
    OUTREACH_QUEUE_HEADERS,
    build_outreach_queue_csv,
    build_raw_candidates_csv,
)
from .exports.google_sheets import append_rows_to_google_sheets
from .scoring.engine import evaluate_candidate
from .sources.funding_news import fetch_candidates as fetch_funding_candidates
from .sources.github_signals import fetch_candidates as fetch_github_candidates
from .sources.hiring_signals import fetch_candidates as fetch_hiring_candidates

app = typer.Typer(help="Leady backend CLI")
console = Console()


def _parse_sources(sources: str) -> list[str]:
    allowed = {"funding", "hiring", "github"}
    names = [item.strip().lower() for item in sources.split(",") if item.strip()]
    if not names:
        raise typer.BadParameter("--sources must include at least one source")
    invalid = [name for name in names if name not in allowed]
    if invalid:
        raise typer.BadParameter(f"Unknown sources: {', '.join(invalid)}")
    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        if name not in seen:
            ordered.append(name)
            seen.add(name)
    return ordered


def _discover_candidates(days: int, sources: list[str]) -> list[RawCandidate]:
    since = (datetime.now(tz=UTC) - timedelta(days=days)).date().isoformat()
    candidates: list[RawCandidate] = []
    if "funding" in sources:
        candidates.extend(
            fetch_funding_candidates(
                [
                    {
                        "company_name": "Acme Analytics",
                        "url": "https://news.example.com/acme-series-a",
                        "text": f"Acme Analytics raised a round on {since} to scale GTM and hiring.",
                    }
                ]
            )
        )
    if "hiring" in sources:
        candidates.extend(
            fetch_hiring_candidates(
                [
                    {
                        "company_name": "Northstar Labs",
                        "url": "https://jobs.example.com/northstar-platform-engineer",
                        "description": "Hiring platform and backend engineers to build developer tooling.",
                    }
                ]
            )
        )
    if "github" in sources:
        candidates.extend(
            fetch_github_candidates(
                [
                    {
                        "company_name": "Acme Analytics",
                        "url": "https://github.com/acme/infra",
                        "stars": 210,
                    }
                ]
            )
        )
    return candidates


@app.command()
def version() -> None:
    """Print package version."""
    typer.echo(__version__)


@app.command()
def run(
    days: int = typer.Option(30, "--days", min=1, help="Only process candidates discovered in the last N days"),
    sources: str = typer.Option("funding,hiring,github", "--sources", help="Comma-separated sources"),
    include_unknown_stage: bool = typer.Option(
        False,
        "--include-unknown-stage",
        help="Include unknown-stage companies in outreach exports",
    ),
) -> None:
    """Run pipeline orchestration: discovery -> dedup -> enrichment -> scoring -> export."""
    selected_sources = _parse_sources(sources)

    with get_connection() as conn:
        run_id = create_run(conn, user_id=None, status=RunStatus.running)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Starting run", total=5)

        progress.update(task, description="Discovery")
        discovered = _discover_candidates(days=days, sources=selected_sources)
        progress.advance(task)

        progress.update(task, description="Dedup + Persist")
        with get_connection() as conn:
            for candidate in discovered:
                persist_raw_candidate(conn, run_id, candidate)
            persisted = list_companies(conn, run_id=run_id)
        progress.advance(task)

        progress.update(task, description="Enrichment")
        enriched = [enrich_candidate(company_to_candidate) for company_to_candidate in (
            RawCandidate(
                company_name=company.name,
                domain=company.domain,
                source_type=SourceType.website,
                source_url=str(company.metadata.get("source_url", "")) or None,
                metadata=company.metadata,
            )
            for company in persisted
        )]
        progress.advance(task)

        progress.update(task, description="Scoring")
        with get_connection() as conn:
            for company, candidate in zip(persisted, enriched, strict=False):
                evaluation = evaluate_candidate(candidate)
                upsert_company(
                    conn,
                    Company(
                        run_id=run_id,
                        name=company.name,
                        domain=candidate.domain,
                        industry=company.industry,
                        employee_count=company.employee_count,
                        location=company.location,
                        score=float(evaluation["score"]),
                        metadata={**company.metadata, **candidate.metadata, **evaluation},
                    ),
                )
            update_run_status(conn, run_id, RunStatus.completed)
            scored_companies = list_companies(conn, run_id=run_id)
        progress.advance(task)

        progress.update(task, description="Export")
        content = build_outreach_queue_csv(scored_companies, include_unknown_stage=include_unknown_stage)
        output = Path("backend/.data") / f"outreach_queue_run_{run_id}.csv"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        progress.advance(task)

    console.print(
        f"[green]run complete[/green] run_id={run_id} candidates={len(discovered)} exported={output}",
    )


@app.command()
def enrich(run_id: int = typer.Option(..., "--run-id", min=1, help="Run id to enrich")) -> None:
    """Enrich all companies for a run and persist metadata updates."""
    with get_connection() as conn:
        companies = list_companies(conn, run_id=run_id)
        for company in companies:
            candidate = RawCandidate(
                company_name=company.name,
                domain=company.domain,
                source_type=SourceType.website,
                source_url=str(company.metadata.get("source_url", "")) or None,
                metadata=company.metadata,
            )
            enriched = enrich_candidate(candidate)
            upsert_company(
                conn,
                Company(
                    run_id=run_id,
                    name=company.name,
                    domain=enriched.domain,
                    industry=company.industry,
                    employee_count=company.employee_count,
                    location=company.location,
                    score=company.score,
                    metadata=enriched.metadata,
                ),
            )
    typer.echo(f"enriched {len(companies)} companies for run {run_id}")


@app.command()
def export(
    output: Path = typer.Option(..., "--output", "-o", help="Output CSV path"),
    run_id: int | None = typer.Option(None, "--run-id", help="Filter rows by run id"),
    export_type: str = typer.Option("outreach", "--type", help="outreach or raw"),
    include_unknown_stage: bool = typer.Option(False, "--include-unknown-stage", help="Include unknown stage rows"),
) -> None:
    """Export outreach_queue.csv or raw_candidates.csv."""
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


@app.command()
def stats() -> None:
    """Print run and company stats from DB."""
    with get_connection() as conn:
        runs = list_runs(conn)
        companies = list_companies(conn)
    avg_score = round(sum(company.score for company in companies) / len(companies), 2) if companies else 0.0
    typer.echo(
        f"runs={len(runs)} companies={len(companies)} completed_runs={len([r for r in runs if r.status == RunStatus.completed])} average_score={avg_score}"
    )


@app.command("create-user")
def create_user_command(
    email: str = typer.Option(..., "--email", help="User email"),
    full_name: str | None = typer.Option(None, "--full-name", help="Full name"),
) -> None:
    """Create a user in the backing database."""
    with get_connection() as conn:
        created = create_user(conn, User(email=email, full_name=full_name))
    typer.echo(f"created user id={created.id} email={created.email}")


@app.command()
def serve(
    host: str = typer.Option(None, "--host", help="Bind host"),
    port: int = typer.Option(None, "--port", help="Bind port"),
) -> None:
    """Start API server (includes MCP mount in same process)."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(api_app, host=host or settings.api.host, port=port or settings.api.port)


@app.command("mcp-serve")
def mcp_serve(
    host: str = typer.Option(None, "--host", help="Bind host"),
    port: int = typer.Option(None, "--port", help="Bind port"),
) -> None:
    """Start unified API+MCP server (MCP served at /mcp)."""
    serve(host=host, port=port)


@app.command("export-csv")
def export_csv_legacy(
    output: Path = typer.Option(..., "--output", "-o", help="Output CSV path"),
    run_id: int | None = typer.Option(None, "--run-id", help="Filter rows by run id"),
    export_type: str = typer.Option("outreach", "--type", help="outreach or raw"),
    include_unknown_stage: bool = typer.Option(False, help="Include rows with unknown stage in outreach"),
) -> None:
    """Backward compatible alias for `export`."""
    export(output=output, run_id=run_id, export_type=export_type, include_unknown_stage=include_unknown_stage)


def main(argv: list[str] | None = None) -> int:
    """Entry point used by `python -m leadbot` and tests."""
    try:
        app(args=argv, standalone_mode=False)
    except SystemExit as exc:
        return int(exc.code)
    return 0
