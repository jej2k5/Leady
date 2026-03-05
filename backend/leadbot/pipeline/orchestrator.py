from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from ..db.models import Company, RawCandidate, RunStatus, SourceType
from ..db.queries import list_companies, persist_raw_candidate, update_run_status, upsert_company
from ..db.session import get_connection
from ..enrichment.pipeline import enrich_candidate
from ..exports.csv_export import build_outreach_queue_csv
from ..scoring.engine import evaluate_candidate
from ..sources.funding_news import fetch_candidates as fetch_funding_candidates
from ..sources.github_signals import fetch_candidates as fetch_github_candidates
from ..sources.hiring_signals import fetch_candidates as fetch_hiring_candidates


def parse_sources(sources: str) -> list[str]:
    allowed = {"funding", "hiring", "github"}
    names = [item.strip().lower() for item in sources.split(",") if item.strip()]
    if not names:
        raise ValueError("sources must include at least one source")
    invalid = [name for name in names if name not in allowed]
    if invalid:
        raise ValueError(f"Unknown sources: {', '.join(invalid)}")

    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        if name in seen:
            continue
        ordered.append(name)
        seen.add(name)

    return ordered


def discover_candidates(days: int, sources: list[str]) -> list[RawCandidate]:
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


def run_pipeline_for_run(
    run_id: int,
    *,
    days: int = 30,
    sources: str = "funding,hiring,github",
    include_unknown_stage: bool = False,
) -> None:
    selected_sources = parse_sources(sources)

    try:
        with get_connection() as conn:
            update_run_status(conn, run_id, RunStatus.running)

        discovered = discover_candidates(days=days, sources=selected_sources)

        with get_connection() as conn:
            for candidate in discovered:
                persist_raw_candidate(conn, run_id, candidate)
            persisted = list_companies(conn, run_id=run_id)

        enriched = [
            enrich_candidate(
                RawCandidate(
                    company_name=company.name,
                    domain=company.domain,
                    source_type=SourceType.website,
                    source_url=str(company.metadata.get("source_url", "")) or None,
                    metadata=company.metadata,
                )
            )
            for company in persisted
        ]

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

        content = build_outreach_queue_csv(scored_companies, include_unknown_stage=include_unknown_stage)
        output = Path("backend/.data") / f"outreach_queue_run_{run_id}.csv"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    except Exception:
        with get_connection() as conn:
            update_run_status(conn, run_id, RunStatus.failed)
        raise
