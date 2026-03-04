"""Text normalization and signal extraction helpers."""

from __future__ import annotations

import re
from collections import Counter

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
}

DEVELOPER_SIGNAL_TERMS = {
    "api",
    "sdk",
    "developer",
    "engineering",
    "graphql",
    "integration",
    "platform",
    "repository",
    "devops",
}


def clean_text(text: str) -> str:
    """Collapse noisy whitespace and strip simple markup-ish artifacts."""
    stripped = re.sub(r"<[^>]+>", " ", text)
    normalized = re.sub(r"\s+", " ", stripped)
    return normalized.strip()


def extract_keywords(text: str, *, limit: int = 10) -> list[str]:
    """Return top-frequency non-trivial tokens."""
    cleaned = clean_text(text).lower()
    tokens = re.findall(r"[a-z0-9][a-z0-9\-]{2,}", cleaned)
    filtered = [token for token in tokens if token not in STOP_WORDS]
    return [token for token, _ in Counter(filtered).most_common(limit)]


def has_developer_signal(text: str) -> bool:
    """Detect if text suggests developer-centric product motion."""
    lowered = clean_text(text).lower()
    return any(term in lowered for term in DEVELOPER_SIGNAL_TERMS)
