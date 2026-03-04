"""Lead classification heuristics."""

from __future__ import annotations

from ..db.models import RawCandidate, SignalType


def classify_candidate(candidate: RawCandidate) -> str:
    """Classify candidate by strongest observed signal."""
    types = {signal.signal_type for signal in candidate.signals}
    if SignalType.funding in types and SignalType.hiring in types:
        return "hot"
    if SignalType.funding in types or SignalType.hiring in types:
        return "warm"
    if SignalType.technology in types:
        return "builder"
    return "cold"
