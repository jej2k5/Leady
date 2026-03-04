from __future__ import annotations

from leadbot.config import get_settings
from leadbot.db.models import RawCandidate, Signal, SignalType, SourceType
from leadbot.scoring.scorer import score_candidate


def test_score_candidate_applies_weights_and_bounds() -> None:
    candidate = RawCandidate(
        company_name="Acme",
        source_type=SourceType.api,
        signals=[
            Signal(company_id=0, signal_type=SignalType.intent, value="high_intent", confidence=2.0),
            Signal(company_id=0, signal_type=SignalType.hiring, value="active_hiring", confidence=-0.5),
        ],
    )
    assert score_candidate(candidate) == 35.0


def test_score_candidate_caps_to_max_score() -> None:
    candidate = RawCandidate(
        company_name="Big",
        source_type=SourceType.api,
        signals=[Signal(company_id=0, signal_type=SignalType.intent, value=f"v{i}", confidence=1.0) for i in range(5)],
    )
    assert score_candidate(candidate) == get_settings().scoring.max_score
