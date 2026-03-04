"""Candidate enrichment pipeline."""

from __future__ import annotations

from ..db.models import RawCandidate
from .crawler import fetch_page_text
from .domain import infer_company_domain
from .email_extractor import extract_emails
from .one_liner import generate_one_liner


def enrich_candidate(candidate: RawCandidate) -> RawCandidate:
    """Fill optional domain and enrichment metadata from source URL."""
    metadata = dict(candidate.metadata)
    if candidate.source_url:
        metadata.setdefault("domain", infer_company_domain(candidate.source_url))
        page_text = fetch_page_text(candidate.source_url)
        metadata["one_liner"] = generate_one_liner(candidate.company_name, page_text)
        emails = extract_emails(page_text)
        if emails:
            metadata["emails"] = ",".join(emails)

    domain = candidate.domain or str(metadata.get("domain") or "") or None
    return candidate.model_copy(update={"domain": domain, "metadata": metadata})
