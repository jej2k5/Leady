"""GitHub-orgs provider normalization adapter."""

from __future__ import annotations

from typing import Any


def _as_non_negative_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(0, value)
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return 0
    return max(0, parsed)


def normalize_github_org_signal(signal: dict[str, Any], *, default_source: str = "github_orgs") -> dict[str, Any] | None:
    """Normalize one GitHub signal row into pipeline seed format."""
    company_name = str(signal.get("company_name") or signal.get("company") or signal.get("org_name") or "").strip()
    if not company_name:
        return None

    return {
        "company_name": company_name,
        "url": str(signal.get("url") or signal.get("repo_url") or signal.get("org_url") or "").strip(),
        "stars": _as_non_negative_int(signal.get("stars")),
        "repo_count": _as_non_negative_int(signal.get("repo_count") or signal.get("repos")),
        "source": str(signal.get("source") or default_source).strip() or default_source,
    }


def fetch_github_org_signals(query_config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Fetch (from query config) and normalize GitHub org/repo rows."""
    config = query_config or {}
    rows = config.get("rows") or config.get("repos") or config.get("orgs") or config.get("seed") or []
    if not isinstance(rows, list):
        return []

    normalized: list[dict[str, Any]] = []
    source = str(config.get("source") or "github_orgs")
    for row in rows:
        if not isinstance(row, dict):
            continue
        normalized_row = normalize_github_org_signal(row, default_source=source)
        if normalized_row:
            normalized.append(normalized_row)
    return normalized
