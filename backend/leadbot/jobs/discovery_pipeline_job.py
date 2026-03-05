"""Automation job for discovery-driven pipeline starts."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..db.models import RunStatus
from ..db.queries import create_discovery_pipeline_job_run, create_run, update_run_status
from ..db.session import get_connection
from ..discovery.filters import evaluate_category_signals
from ..discovery.orchestrator import discover_seed_data
from ..pipeline.orchestrator import run_pipeline_for_run
from ..utils.dedup import normalize_domain

SourceSeedData = dict[str, list[dict[str, Any]]]


class DiscoveryPipelineConfig(BaseModel):
    days: int = Field(default=30, ge=1, le=365)
    sources: str = "funding,hiring,github"
    categories: list[str] = Field(default_factory=list)
    max_candidates: int = Field(default=25, ge=1, le=1000)


def _candidate_text(row: dict[str, Any]) -> list[str]:
    values = [str(row.get("company_name") or ""), str(row.get("url") or "")]
    for key in ("text", "description"):
        if row.get(key):
            values.append(str(row[key]))
    return values


def _row_sort_key(row: dict[str, Any]) -> tuple[int, int]:
    stars = row.get("stars") if isinstance(row.get("stars"), int) else 0
    signal_len = len(str(row.get("text") or row.get("description") or ""))
    return (stars, signal_len)


def _build_seed_payload(discovered: SourceSeedData, config: DiscoveryPipelineConfig) -> tuple[SourceSeedData, int]:
    allowed_categories = {item.strip().lower() for item in config.categories if item.strip()}
    source_seed_data: SourceSeedData = {"funding": [], "hiring": [], "github": []}
    seen_keys: set[str] = set()
    scanned = 0

    for source in source_seed_data:
        rows = discovered.get(source, [])
        ordered_rows = sorted(rows, key=_row_sort_key, reverse=True)
        for row in ordered_rows:
            if len(source_seed_data[source]) >= config.max_candidates:
                break
            scanned += 1

            text_blobs = _candidate_text(row)
            if allowed_categories:
                decision = evaluate_category_signals(text_blobs)
                if not (set(decision.matched_categories) & allowed_categories):
                    continue

            dedupe_key = normalize_domain(str(row.get("url") or "")) or str(row.get("company_name") or "").strip().lower()
            if not dedupe_key or dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)

            seed_row: dict[str, Any] = {
                "company_name": str(row.get("company_name") or "").strip(),
                "url": str(row.get("url") or "").strip(),
            }
            if source == "funding":
                seed_row["text"] = str(row.get("text") or "")
                if row.get("published_at"):
                    seed_row["published_at"] = row.get("published_at")
            elif source == "hiring":
                seed_row["description"] = str(row.get("description") or "")
                if row.get("posted_at"):
                    seed_row["posted_at"] = row.get("posted_at")
            else:
                seed_row["stars"] = row.get("stars") if isinstance(row.get("stars"), int) else 0
                if isinstance(row.get("repo_count"), int):
                    seed_row["repo_count"] = row.get("repo_count")

            if seed_row["company_name"]:
                source_seed_data[source].append(seed_row)

    return source_seed_data, scanned


def run_discovery_pipeline_job(
    config: DiscoveryPipelineConfig,
    *,
    user_id: int | None = None,
) -> dict[str, int | str]:
    source_names = [item.strip().lower() for item in config.sources.split(",") if item.strip()]
    discovery_config = {name: {"days": config.days, "max_candidates": config.max_candidates} for name in source_names}

    discovered = discover_seed_data(discovery_config)
    source_seed_data, candidates_scanned = _build_seed_payload(discovered, config)
    seeded_count = sum(len(rows) for rows in source_seed_data.values())

    with get_connection() as conn:
        run_id = create_run(conn, user_id=user_id)

    try:
        run_pipeline_for_run(
            run_id,
            days=config.days,
            sources=config.sources,
            include_unknown_stage=False,
            source_seed_data=source_seed_data,
        )
    except Exception as exc:
        with get_connection() as conn:
            update_run_status(conn, run_id, RunStatus.failed)
            create_discovery_pipeline_job_run(
                conn,
                run_id=run_id,
                candidates_scanned=candidates_scanned,
                seeded_count=seeded_count,
                status="failed",
                error=str(exc),
            )
        raise

    with get_connection() as conn:
        create_discovery_pipeline_job_run(
            conn,
            run_id=run_id,
            candidates_scanned=candidates_scanned,
            seeded_count=seeded_count,
            status="completed",
        )

    return {"run_id": run_id, "candidates_scanned": candidates_scanned, "seeded_count": seeded_count, "status": "queued"}
