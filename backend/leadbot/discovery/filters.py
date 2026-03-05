"""Keyword-based category filtering for discovery candidates."""

from __future__ import annotations

from dataclasses import dataclass

CATEGORY_KEYWORDS: dict[str, set[str]] = {
    "ai_infra": {
        "ai infrastructure",
        "llmops",
        "model serving",
        "model inference",
        "vector database",
        "rag",
        "gpu cloud",
        "inference platform",
    },
    "devops": {
        "devops",
        "platform engineering",
        "ci/cd",
        "continuous integration",
        "observability",
        "kubernetes",
        "infra automation",
        "developer platform",
    },
    "secops": {
        "secops",
        "cloud security",
        "threat detection",
        "security operations",
        "soar",
        "siem",
        "application security",
        "runtime security",
    },
    "integration": {
        "api integration",
        "workflow automation",
        "ipaas",
        "integration platform",
        "zapier",
        "event-driven integration",
        "enterprise integration",
    },
    "data_integration": {
        "etl",
        "elt",
        "reverse etl",
        "data pipeline",
        "data integration",
        "cdc",
        "data sync",
        "data movement",
    },
}


@dataclass(slots=True)
class CategoryDecision:
    has_strong_signal: bool
    matched_categories: list[str]
    matched_keywords: dict[str, list[str]]


def evaluate_category_signals(text_blobs: list[str]) -> CategoryDecision:
    corpus = " ".join(blob.lower() for blob in text_blobs if blob).strip()
    matched_keywords: dict[str, list[str]] = {}

    if not corpus:
        return CategoryDecision(False, [], matched_keywords)

    for category, keywords in CATEGORY_KEYWORDS.items():
        hits = sorted([keyword for keyword in keywords if keyword in corpus])
        if hits:
            matched_keywords[category] = hits

    matched_categories = sorted(matched_keywords)
    return CategoryDecision(
        has_strong_signal=bool(matched_categories),
        matched_categories=matched_categories,
        matched_keywords=matched_keywords,
    )
