"""GitHub-orgs provider normalization adapter."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import requests


_DEFAULT_CACHE_PATH = Path(".cache/github_orgs_cache.json")
_GITHUB_API_BASE = "https://api.github.com"


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


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _load_cache(cache_path: Path) -> dict[str, Any]:
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(cache_path: Path, payload: dict[str, Any]) -> None:
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(payload), encoding="utf-8")
    except OSError:
        return


def _cache_key(org_login: str, repo_limit: int) -> str:
    return f"{org_login.lower()}::{max(repo_limit, 1)}"


def _github_get_json(
    session: requests.Session,
    url: str,
    *,
    headers: dict[str, str],
    timeout_seconds: float,
) -> tuple[dict[str, Any] | list[dict[str, Any]] | None, bool]:
    """Return JSON payload and whether the rate-limit has been hit."""
    try:
        response = session.get(url, headers=headers, timeout=timeout_seconds)
    except requests.RequestException:
        return None, False

    if response.status_code == 403:
        if response.headers.get("X-RateLimit-Remaining") == "0":
            return None, True
        return None, False
    if response.status_code == 404:
        return None, False
    if response.status_code >= 400:
        return None, False

    try:
        payload = response.json()
    except ValueError:
        return None, False
    return payload, False


def _topic_feature_counts(repos: list[dict[str, Any]]) -> dict[str, int]:
    groups = {
        "security": {"security", "secops", "sast", "dast", "vulnerability", "compliance", "soc2"},
        "devops": {"devops", "platform-engineering", "kubernetes", "terraform", "iac", "ci", "cd", "sre"},
        "integration": {"integration", "sdk", "api", "webhook", "connector", "middleware", "etl"},
    }
    counts = {k: 0 for k in groups}
    for repo in repos:
        topics = repo.get("topics") if isinstance(repo.get("topics"), list) else []
        normalized = {str(topic).strip().lower() for topic in topics if str(topic).strip()}
        for label, needles in groups.items():
            if normalized.intersection(needles):
                counts[label] += 1
    return counts


def _fetch_org_bundle(
    org_login: str,
    *,
    session: requests.Session,
    headers: dict[str, str],
    timeout_seconds: float,
    top_repos: int,
) -> tuple[dict[str, Any] | None, bool]:
    org_url = f"{_GITHUB_API_BASE}/orgs/{org_login}"
    org_payload_raw, limited = _github_get_json(session, org_url, headers=headers, timeout_seconds=timeout_seconds)
    if limited:
        return None, True
    if not isinstance(org_payload_raw, dict):
        return None, False

    repos_url = (
        f"{_GITHUB_API_BASE}/orgs/{org_login}/repos"
        f"?sort=updated&per_page={max(top_repos, 1)}&type=public"
    )
    repos_payload_raw, limited = _github_get_json(session, repos_url, headers=headers, timeout_seconds=timeout_seconds)
    if limited:
        return None, True
    repos_payload = repos_payload_raw if isinstance(repos_payload_raw, list) else []

    repos: list[dict[str, Any]] = []
    for repo in repos_payload:
        if not isinstance(repo, dict):
            continue
        repos.append(
            {
                "name": str(repo.get("name") or "").strip(),
                "url": str(repo.get("html_url") or "").strip(),
                "stars": _as_non_negative_int(repo.get("stargazers_count")),
                "pushed_at": str(repo.get("pushed_at") or "").strip(),
                "description": str(repo.get("description") or "").strip(),
                "topics": repo.get("topics") if isinstance(repo.get("topics"), list) else [],
            }
        )

    return {
        "org": {
            "login": str(org_payload_raw.get("login") or org_login).strip(),
            "name": str(org_payload_raw.get("name") or org_login).strip(),
            "url": str(org_payload_raw.get("html_url") or "").strip(),
            "description": str(org_payload_raw.get("description") or "").strip(),
            "public_repos": _as_non_negative_int(org_payload_raw.get("public_repos")),
        },
        "repos": repos,
    }, False


def _map_org_bundle_to_seed_rows(bundle: dict[str, Any], *, source: str, recent_days: int, min_repo_stars: int) -> list[dict[str, Any]]:
    org = bundle.get("org") if isinstance(bundle.get("org"), dict) else {}
    repos = bundle.get("repos") if isinstance(bundle.get("repos"), list) else []
    if not repos:
        return []

    now = datetime.now(UTC)
    cutoff = now - timedelta(days=max(recent_days, 1))
    recent_push_count = 0
    aggregate_stars = 0
    valid_repos: list[dict[str, Any]] = []
    for repo in repos:
        if not isinstance(repo, dict):
            continue
        stars = _as_non_negative_int(repo.get("stars"))
        pushed_at = _parse_datetime(repo.get("pushed_at"))
        if pushed_at and pushed_at >= cutoff:
            recent_push_count += 1
        aggregate_stars += stars
        valid_repos.append(repo)

    if not valid_repos:
        return []

    topic_features = _topic_feature_counts(valid_repos)
    org_name = str(org.get("name") or org.get("login") or "").strip()
    org_url = str(org.get("url") or "").strip()
    repo_count = len(valid_repos)

    rows: list[dict[str, Any]] = []
    for repo in valid_repos:
        repo_stars = _as_non_negative_int(repo.get("stars"))
        if repo_stars < max(min_repo_stars, 0) and not rows:
            # Always keep at least one row for qualified orgs.
            pass
        elif repo_stars < max(min_repo_stars, 0):
            continue
        rows.append(
            {
                "company_name": org_name,
                "url": str(repo.get("url") or org_url),
                "stars": repo_stars,
                "repo_count": repo_count,
                "source": source,
                "org_login": str(org.get("login") or ""),
                "org_url": org_url,
                "org_description": str(org.get("description") or ""),
                "repo_name": str(repo.get("name") or ""),
                "repo_description": str(repo.get("description") or ""),
                "repo_pushed_at": str(repo.get("pushed_at") or ""),
                "repo_topics": repo.get("topics") if isinstance(repo.get("topics"), list) else [],
                "aggregate_stars": aggregate_stars,
                "recent_push_count": recent_push_count,
                "topic_security_count": topic_features["security"],
                "topic_devops_count": topic_features["devops"],
                "topic_integration_count": topic_features["integration"],
            }
        )
    return rows


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
    """Fetch (from query config and GitHub API) and normalize GitHub org/repo rows."""
    config = query_config or {}
    source = str(config.get("source") or "github_orgs")

    rows = config.get("rows") or config.get("repos") or config.get("seed") or []
    normalized: list[dict[str, Any]] = []
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            normalized_row = normalize_github_org_signal(row, default_source=source)
            if normalized_row:
                normalized.append(normalized_row)

    org_entries = config.get("orgs") or []
    if not isinstance(org_entries, list) or not org_entries:
        return normalized

    top_repos = _as_non_negative_int(config.get("top_repos") or 5) or 5
    min_repo_stars = _as_non_negative_int(config.get("min_repo_stars") or 0)
    recent_days = _as_non_negative_int(config.get("recent_days") or 30) or 30
    min_recent_pushes = _as_non_negative_int(config.get("min_recent_pushes") or 1)
    min_aggregate_stars = _as_non_negative_int(config.get("min_aggregate_stars") or 20)
    timeout_seconds = float(config.get("timeout_seconds") or 8)
    cache_path = Path(str(config.get("cache_path") or _DEFAULT_CACHE_PATH))

    token = str(config.get("token") or os.getenv("GITHUB_TOKEN") or "").strip()
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    cache = _load_cache(cache_path)
    today = datetime.now(UTC).date().isoformat()

    session = requests.Session()
    rate_limited = False

    for org_entry in org_entries:
        org_login = str(org_entry.get("login") if isinstance(org_entry, dict) else org_entry).strip()
        if not org_login:
            continue
        cache_entry = cache.get(_cache_key(org_login, top_repos)) if isinstance(cache, dict) else None
        bundle: dict[str, Any] | None = None
        if isinstance(cache_entry, dict) and cache_entry.get("date") == today and isinstance(cache_entry.get("bundle"), dict):
            bundle = cache_entry["bundle"]
        else:
            bundle, limited = _fetch_org_bundle(
                org_login,
                session=session,
                headers=headers,
                timeout_seconds=timeout_seconds,
                top_repos=top_repos,
            )
            if limited:
                rate_limited = True
                break
            if bundle is None:
                continue
            cache[_cache_key(org_login, top_repos)] = {"date": today, "bundle": bundle}

        mapped_rows = _map_org_bundle_to_seed_rows(
            bundle,
            source=source,
            recent_days=recent_days,
            min_repo_stars=min_repo_stars,
        )
        if not mapped_rows:
            continue

        org_features = mapped_rows[0]
        qualifies = (
            _as_non_negative_int(org_features.get("recent_push_count")) >= min_recent_pushes
            or _as_non_negative_int(org_features.get("aggregate_stars")) >= min_aggregate_stars
            or _as_non_negative_int(org_features.get("topic_security_count")) > 0
            or _as_non_negative_int(org_features.get("topic_devops_count")) > 0
            or _as_non_negative_int(org_features.get("topic_integration_count")) > 0
        )
        if qualifies:
            normalized.extend(mapped_rows)

    _save_cache(cache_path, cache)

    if rate_limited:
        return normalized
    return normalized
