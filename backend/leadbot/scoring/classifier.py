"""Lead classification heuristics."""

from __future__ import annotations

from ..db.models import RawCandidate, SignalType


def classify_candidate(candidate: RawCandidate) -> str:
    """Classify candidate by strongest observed signal."""
    strengths: dict[SignalType, float] = {}
    for signal in candidate.signals:
        strengths[signal.signal_type] = max(strengths.get(signal.signal_type, 0.0), signal.confidence)

    if SignalType.intent in strengths and strengths[SignalType.intent] >= 0.7:
        return "hot"
    if SignalType.funding in strengths and SignalType.hiring in strengths:
        return "hot"
    if SignalType.funding in strengths or SignalType.hiring in strengths:
        return "warm"
    if SignalType.technology in strengths:
        return "builder"
    return "cold"
