"""Canonical deduplication and company persistence flow."""

from __future__ import annotations

import sqlite3
from urllib.parse import urlparse

from ..db.models import Company, RawCandidate


def normalize_domain(domain: str | None) -> str | None:
    """Normalize domains to a host-only lowercase form."""
    if not domain:
        return None

    candidate = domain.strip().lower()
    if not candidate:
        return None

    if "@" in candidate and "/" not in candidate and "://" not in candidate:
        candidate = candidate.split("@", 1)[1]

    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    host = parsed.netloc or parsed.path
    host = host.split("/", 1)[0].split(":", 1)[0].strip(".")
    if host.startswith("www."):
        host = host[4:]
    return host or None


def upsert_candidate_company(conn: sqlite3.Connection, run_id: int, candidate: RawCandidate) -> Company:
    """Only supported write-path for candidate company records."""
    from ..db import queries

    clean_name = candidate.company_name.strip()
    if not clean_name:
        raise ValueError("Candidate company_name is required")

    company = queries.upsert_company(
        conn,
        Company(
            run_id=run_id,
            name=clean_name,
            domain=normalize_domain(candidate.domain),
            metadata=candidate.metadata,
        ),
    )
    if company.id is None:
        raise ValueError("Persisted company is missing an id")

    source_id = queries.upsert_source(conn, company.id, candidate.source_type.value, candidate.source_url)
    for signal in candidate.signals:
        queries.upsert_signal(conn, signal.model_copy(update={"company_id": company.id, "source_id": source_id}))
    for contact in candidate.contacts:
        queries.upsert_contact(conn, contact.model_copy(update={"company_id": company.id}))
    return company
