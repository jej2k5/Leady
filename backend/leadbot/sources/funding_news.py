"""Funding-news based source adapter."""

from __future__ import annotations

from ..db.models import RawCandidate, Signal, SignalType, SourceType
from ..utils.text import extract_keywords


def build_funding_candidate(company_name: str, article_url: str, article_text: str) -> RawCandidate:
    """Create a candidate inferred from funding-news content."""
    keywords = extract_keywords(article_text, limit=6)
    return RawCandidate(
        company_name=company_name.strip(),
        domain=None,
        source_type=SourceType.website,
        source_url=article_url,
        signals=[
            Signal(
                company_id=0,
                source_id=None,
                signal_type=SignalType.funding,
                value="recent_funding_mentioned",
                confidence=0.75,
            )
        ],
        metadata={"keywords": ",".join(keywords), "source": "funding_news"},
    )


def fetch_candidates(seed_articles: list[dict[str, str]]) -> list[RawCandidate]:
    """Build candidates from pre-fetched funding news articles."""
    candidates: list[RawCandidate] = []
    for article in seed_articles:
        name = article.get("company_name", "").strip()
        if not name:
            continue
        candidates.append(
            build_funding_candidate(
                company_name=name,
                article_url=article.get("url", ""),
                article_text=article.get("text", ""),
            )
        )
    return candidates
