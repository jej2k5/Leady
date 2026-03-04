"""Utility namespace exports."""

from .dedup import normalize_domain, upsert_candidate_company
from .http import ThrottledSession, build_throttled_session
from .text import clean_text, extract_keywords, has_developer_signal

__all__ = [
    "ThrottledSession",
    "build_throttled_session",
    "clean_text",
    "extract_keywords",
    "has_developer_signal",
    "normalize_domain",
    "upsert_candidate_company",
]
