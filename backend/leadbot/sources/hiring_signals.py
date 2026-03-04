"""Hiring-signal source adapter."""

from __future__ import annotations

from ..db.models import RawCandidate, Signal, SignalType, SourceType
from ..utils.text import has_developer_signal


def build_hiring_candidate(company_name: str, job_post_url: str, job_description: str) -> RawCandidate:
    """Create a candidate from a hiring post."""
    confidence = 0.8 if has_developer_signal(job_description) else 0.55
    return RawCandidate(
        company_name=company_name,
        source_type=SourceType.directory,
        source_url=job_post_url,
        signals=[
            Signal(
                company_id=0,
                source_id=None,
                signal_type=SignalType.hiring,
                value="active_hiring",
                confidence=confidence,
            )
        ],
        metadata={"developer_hiring": has_developer_signal(job_description)},
    )


def fetch_candidates(job_posts: list[dict[str, str]]) -> list[RawCandidate]:
    """Build candidates from pre-collected job-post entries."""
    candidates: list[RawCandidate] = []
    for post in job_posts:
        name = post.get("company_name", "").strip()
        if not name:
            continue
        candidates.append(
            build_hiring_candidate(
                company_name=name,
                job_post_url=post.get("url", ""),
                job_description=post.get("description", ""),
            )
        )
    return candidates
