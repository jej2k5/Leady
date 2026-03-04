from __future__ import annotations

from leadbot.db.models import RawCandidate, Signal, SignalType, SourceType
from leadbot.scoring.classifier import classify_candidate


def _candidate(*signal_types: SignalType) -> RawCandidate:
    return RawCandidate(
        company_name="Acme",
        source_type=SourceType.api,
        signals=[Signal(company_id=0, signal_type=kind, value=kind.value, confidence=0.5) for kind in signal_types],
    )


def test_classify_candidate_priority() -> None:
    assert classify_candidate(_candidate(SignalType.funding, SignalType.hiring)) == "hot"
    assert classify_candidate(_candidate(SignalType.hiring)) == "warm"
    assert classify_candidate(_candidate(SignalType.technology)) == "builder"
    assert classify_candidate(_candidate()) == "cold"
