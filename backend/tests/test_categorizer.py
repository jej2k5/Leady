from __future__ import annotations

from leadbot.db.models import RawCandidate, Signal, SignalType, SourceType
from leadbot.scoring.categorizer import categorize_candidate


def test_categorize_candidate_prefers_developer_signal() -> None:
    candidate = RawCandidate(
        company_name="Acme",
        source_type=SourceType.website,
        metadata={"description": "API platform for engineering teams"},
        signals=[Signal(company_id=0, signal_type=SignalType.funding, value="recent_funding_seed", confidence=0.8)],
    )
    assert categorize_candidate(candidate) == "developer_tooling"


def test_categorize_candidate_funded_then_default() -> None:
    funded = RawCandidate(
        company_name="Funded",
        source_type=SourceType.website,
        signals=[Signal(company_id=0, signal_type=SignalType.funding, value="recent_funding_series_a", confidence=0.8)],
    )
    plain = RawCandidate(company_name="Plain", source_type=SourceType.website)
    assert categorize_candidate(funded) == "funded"
    assert categorize_candidate(plain) == "general_b2b"
