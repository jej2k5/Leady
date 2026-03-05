"""Discovery orchestrator for seed data used by the pipeline."""

from __future__ import annotations

from typing import Any

from ..db.queries import (
    list_discovery_candidates,
    mark_discovery_candidate_seeded,
    upsert_discovery_candidate,
)
from ..db.session import get_connection
from ..utils.dedup import normalize_domain
from .providers.funding_web import fetch_funding_articles
from .providers.github_orgs import fetch_github_org_signals
from .providers.job_boards import fetch_job_posts

SourceSeedData = dict[str, list[dict[str, Any]]]


def _candidate_score(source_group: str, row: dict[str, Any]) -> float:
    if source_group == "funding":
        return 0.85 if row.get("text") else 0.7
    if source_group == "hiring":
        return 0.75 if row.get("description") else 0.6
    stars = row.get("stars") if isinstance(row.get("stars"), int) else 0
    return min(0.95, 0.55 + (max(stars, 0) / 1000))


def _normalize_discovery_domain(url: str | None) -> str | None:
    if not url:
        return None
    return normalize_domain(url)


def _build_seed_from_evidence(source_group: str, evidence: dict[str, Any], company_name: str, source_url: str | None) -> dict[str, Any]:
    payload = evidence.get("payload") if isinstance(evidence.get("payload"), dict) else {}
    seed_row: dict[str, Any] = {"company_name": company_name, "url": source_url or ""}

    if source_group == "funding":
        seed_row["text"] = str(payload.get("text") or "")
        if payload.get("published_at"):
            seed_row["published_at"] = payload.get("published_at")
    elif source_group == "hiring":
        seed_row["description"] = str(payload.get("description") or "")
        if payload.get("posted_at"):
            seed_row["posted_at"] = payload.get("posted_at")
    elif source_group == "github":
        stars = payload.get("stars")
        repo_count = payload.get("repo_count")
        seed_row["stars"] = stars if isinstance(stars, int) else 0
        if isinstance(repo_count, int):
            seed_row["repo_count"] = repo_count

    return seed_row


def discover_seed_data(query_config: dict[str, Any] | None = None) -> SourceSeedData:
    """Collect normalized seed rows from discovery providers and persist findings."""
    config = query_config or {}

    funding_cfg = config.get("funding") if isinstance(config.get("funding"), dict) else {}
    hiring_cfg = config.get("hiring") if isinstance(config.get("hiring"), dict) else {}
    github_cfg = config.get("github") if isinstance(config.get("github"), dict) else {}

    discovered = {
        "funding": fetch_funding_articles(funding_cfg),
        "hiring": fetch_job_posts(hiring_cfg),
        "github": fetch_github_org_signals(github_cfg),
    }

    with get_connection() as conn:
        for source_group, rows in discovered.items():
            for row in rows:
                upsert_discovery_candidate(
                    conn,
                    company_name=str(row.get("company_name") or "").strip(),
                    domain=_normalize_discovery_domain(str(row.get("url") or "")),
                    source_type=source_group,
                    source_url=str(row.get("url") or "").strip() or None,
                    evidence={"source_group": source_group, **row},
                    score=_candidate_score(source_group, row),
                )
    return discovered


def emit_top_unseeded_source_seed_data(limit_per_source: int = 25) -> SourceSeedData:
    """Emit top unseeded discovery candidates as pipeline ``source_seed_data`` payload."""
    if limit_per_source <= 0:
        return {"funding": [], "hiring": [], "github": []}

    grouped: SourceSeedData = {"funding": [], "hiring": [], "github": []}

    with get_connection() as conn:
        candidates = list_discovery_candidates(conn, status="unseeded")
        used_counts = {"funding": 0, "hiring": 0, "github": 0}

        for candidate in candidates:
            candidate_id = int(candidate["id"])
            company_name = str(candidate.get("company_name") or "").strip()
            if not company_name:
                continue

            evidence_rows = candidate.get("evidence") if isinstance(candidate.get("evidence"), list) else []
            selected_any = False
            for evidence in evidence_rows:
                if not isinstance(evidence, dict):
                    continue
                payload = evidence.get("payload") if isinstance(evidence.get("payload"), dict) else {}
                source_group = str(payload.get("source_group") or evidence.get("source_type") or "").strip().lower()
                if source_group not in grouped or used_counts[source_group] >= limit_per_source:
                    continue
                grouped[source_group].append(
                    _build_seed_from_evidence(
                        source_group,
                        evidence,
                        company_name=company_name,
                        source_url=str(evidence.get("source_url") or "").strip() or None,
                    )
                )
                used_counts[source_group] += 1
                selected_any = True

            if selected_any:
                mark_discovery_candidate_seeded(conn, candidate_id)

            if all(count >= limit_per_source for count in used_counts.values()):
                break

    return grouped
