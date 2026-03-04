"""CSV export helpers for outreach and raw-candidate outputs."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable

from ..db.models import Company

OUTREACH_QUEUE_HEADERS = [
    "company_id",
    "run_id",
    "company_name",
    "domain",
    "stage",
    "score",
    "ranking",
]

RAW_CANDIDATES_HEADERS = [
    "company_id",
    "run_id",
    "company_name",
    "domain",
    "stage",
    "score",
    "ranking",
    "metadata_json",
]

_UNKNOWN_STAGE_VALUES = {"", "unknown", "n/a", "na", "undefined", "unclassified"}


def _normalized_stage(company: Company) -> str:
    stage = company.metadata.get("stage") if company.metadata else None
    if stage is None:
        return ""
    return str(stage).strip().lower()


def has_known_stage(company: Company) -> bool:
    """Return whether candidate stage is known enough for outreach queue usage."""
    return _normalized_stage(company) not in _UNKNOWN_STAGE_VALUES


def _ranked_companies(companies: Iterable[Company]) -> list[tuple[int, Company]]:
    ranked = sorted(companies, key=lambda item: (item.score, item.id or 0), reverse=True)
    return [(idx, company) for idx, company in enumerate(ranked, start=1)]


def build_outreach_queue_csv(companies: Iterable[Company], *, include_unknown_stage: bool = False) -> str:
    """Render outreach_queue.csv rows sorted by score with ranking numbers."""
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(OUTREACH_QUEUE_HEADERS)

    for ranking, company in _ranked_companies(companies):
        if not include_unknown_stage and not has_known_stage(company):
            continue

        writer.writerow(
            [
                company.id,
                company.run_id,
                company.name,
                company.domain,
                company.metadata.get("stage", "") if company.metadata else "",
                company.score,
                ranking,
            ]
        )

    return stream.getvalue()


def build_raw_candidates_csv(companies: Iterable[Company]) -> str:
    """Render raw_candidates.csv rows sorted by score with ranking numbers."""
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(RAW_CANDIDATES_HEADERS)

    for ranking, company in _ranked_companies(companies):
        writer.writerow(
            [
                company.id,
                company.run_id,
                company.name,
                company.domain,
                company.metadata.get("stage", "") if company.metadata else "",
                company.score,
                ranking,
                json.dumps(company.metadata, sort_keys=True),
            ]
        )

    return stream.getvalue()
