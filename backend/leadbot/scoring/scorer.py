"""Candidate scoring primitives."""

from __future__ import annotations

from ..config import get_settings
from ..db.models import RawCandidate, SignalType


_SIGNAL_WEIGHTS = {
    SignalType.funding: 30.0,
    SignalType.hiring: 25.0,
    SignalType.technology: 20.0,
    SignalType.intent: 35.0,
}


def score_candidate(candidate: RawCandidate) -> float:
    """Calculate bounded lead score based on observed signals."""
    settings = get_settings()
    score = 0.0
    for signal in candidate.signals:
        weight = _SIGNAL_WEIGHTS.get(signal.signal_type, 10.0)
        confidence = max(min(signal.confidence, 1.0), 0.0)
        score += weight * confidence

    if candidate.domain:
        score += 2.0
    if candidate.contacts:
        score += min(5.0, len(candidate.contacts) * 1.5)

    return min(settings.scoring.max_score, round(score, 2))
