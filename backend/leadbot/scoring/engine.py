"""Lead scoring engine orchestration."""

from __future__ import annotations

from ..db.models import RawCandidate
from .categorizer import categorize_candidate
from .classifier import classify_candidate
from .scorer import score_candidate


def evaluate_candidate(candidate: RawCandidate) -> dict[str, str | float]:
    """Compute score and labels for a candidate."""
    return {
        "classification": classify_candidate(candidate),
        "category": categorize_candidate(candidate),
        "score": score_candidate(candidate),
    }
