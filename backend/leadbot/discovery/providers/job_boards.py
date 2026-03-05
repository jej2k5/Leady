"""Job-boards provider normalization adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _normalize_posted_at(value: Any) -> str | None:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=UTC)
        return dt.isoformat()
    text = str(value).strip()
    return text or None


def normalize_job_post(post: dict[str, Any], *, default_source: str = "job_boards") -> dict[str, Any] | None:
    """Normalize one job-post row into pipeline seed format."""
    company_name = str(post.get("company_name") or post.get("company") or "").strip()
    if not company_name:
        return None

    return {
        "company_name": company_name,
        "url": str(post.get("url") or post.get("link") or "").strip(),
        "description": str(post.get("description") or post.get("text") or "").strip(),
        "posted_at": _normalize_posted_at(post.get("posted_at") or post.get("posted")),
        "source": str(post.get("source") or default_source).strip() or default_source,
    }


def fetch_job_posts(query_config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Fetch (from query config) and normalize job-post rows."""
    config = query_config or {}
    rows = config.get("rows") or config.get("posts") or config.get("seed") or []
    if not isinstance(rows, list):
        return []

    normalized: list[dict[str, Any]] = []
    source = str(config.get("source") or "job_boards")
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized_row = normalize_job_post(row, default_source=source)
        if normalized_row:
            normalized.append(normalized_row)
    return normalized
