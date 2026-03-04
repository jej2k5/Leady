"""Domain inference and normalization helpers."""

from __future__ import annotations

from ..utils.dedup import normalize_domain


def infer_company_domain(url: str | None) -> str | None:
    """Infer normalized domain from an arbitrary URL-like string."""
    return normalize_domain(url)
