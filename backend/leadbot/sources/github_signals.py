"""GitHub-signal source adapter."""

from __future__ import annotations

from ..db.models import RawCandidate, Signal, SignalType, SourceType


def build_github_candidate(company_name: str, repo_url: str, stars: int) -> RawCandidate:
    """Create candidate from GitHub repository activity."""
    bounded_stars = max(stars, 0)
    confidence = min(0.9, 0.4 + min(bounded_stars, 500) / 1000)
    return RawCandidate(
        company_name=company_name.strip(),
        source_type=SourceType.api,
        source_url=repo_url,
        signals=[
            Signal(
                company_id=0,
                source_id=None,
                signal_type=SignalType.technology,
                value="github_project_activity",
                confidence=confidence,
            )
        ],
        metadata={"github_stars": bounded_stars, "source": "github_signals"},
    )


def fetch_candidates(repo_rows: list[dict[str, str | int]]) -> list[RawCandidate]:
    """Build candidates from pre-fetched repository rows."""
    candidates: list[RawCandidate] = []
    for row in repo_rows:
        name = str(row.get("company_name", "")).strip()
        if not name:
            continue
        stars_raw = row.get("stars", 0)
        stars = stars_raw if isinstance(stars_raw, int) else 0
        candidates.append(build_github_candidate(name, str(row.get("url", "")), stars))
    return candidates
