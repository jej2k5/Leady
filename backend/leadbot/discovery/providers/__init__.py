"""Discovery providers."""

from .funding_web import fetch_funding_articles, normalize_funding_article
from .github_orgs import fetch_github_org_signals, normalize_github_org_signal
from .job_boards import fetch_job_posts, normalize_job_post

__all__ = [
    "fetch_funding_articles",
    "normalize_funding_article",
    "fetch_job_posts",
    "normalize_job_post",
    "fetch_github_org_signals",
    "normalize_github_org_signal",
]
