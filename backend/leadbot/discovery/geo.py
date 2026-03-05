"""Geography preference scoring for discovery candidates."""

from __future__ import annotations

from dataclasses import dataclass

_PREFERRED_GEO_TERMS = {
    "us",
    "usa",
    "united states",
    "canada",
    "europe",
    "eu",
    "uk",
    "united kingdom",
    "germany",
    "france",
    "netherlands",
    "spain",
    "sweden",
}


@dataclass(slots=True)
class GeoDecision:
    score_delta: float
    preferred_match: bool
    matched_terms: list[str]


def geography_score(text_blobs: list[str]) -> GeoDecision:
    corpus = " ".join(blob.lower() for blob in text_blobs if blob)
    matched = sorted([term for term in _PREFERRED_GEO_TERMS if term in corpus])
    if matched:
        return GeoDecision(score_delta=0.1, preferred_match=True, matched_terms=matched)
    return GeoDecision(score_delta=0.0, preferred_match=False, matched_terms=[])
