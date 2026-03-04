"""Lead source adapters."""

from .base import gather_candidates
from .funding_news import fetch_candidates as fetch_funding_candidates
from .github_signals import fetch_candidates as fetch_github_candidates
from .hiring_signals import fetch_candidates as fetch_hiring_candidates

__all__ = [
    "gather_candidates",
    "fetch_funding_candidates",
    "fetch_hiring_candidates",
    "fetch_github_candidates",
]
