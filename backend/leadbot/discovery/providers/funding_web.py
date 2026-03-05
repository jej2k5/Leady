"""Funding-web provider normalization adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _normalize_published_at(value: Any) -> str | None:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=UTC)
        return dt.isoformat()
    text = str(value).strip()
    return text or None


def normalize_funding_article(article: dict[str, Any], *, default_source: str = "funding_web") -> dict[str, Any] | None:
    """Normalize one funding article row into pipeline seed format."""
    company_name = str(article.get("company_name") or article.get("company") or "").strip()
    if not company_name:
        return None

    return {
        "company_name": company_name,
        "url": str(article.get("url") or article.get("link") or "").strip(),
        "text": str(article.get("text") or article.get("summary") or "").strip(),
        "published_at": _normalize_published_at(article.get("published_at") or article.get("published")),
        "source": str(article.get("source") or default_source).strip() or default_source,
    }


def fetch_funding_articles(query_config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Fetch (from query config) and normalize funding article rows."""
    config = query_config or {}
    rows = config.get("rows") or config.get("articles") or config.get("seed") or []
    if not isinstance(rows, list):
        return []

    normalized: list[dict[str, Any]] = []
    source = str(config.get("source") or "funding_web")
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized_row = normalize_funding_article(row, default_source=source)
        if normalized_row:
            normalized.append(normalized_row)
    return normalized
