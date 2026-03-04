"""Industry and motion categorization helpers."""

from __future__ import annotations

from ..db.models import RawCandidate
from ..utils.text import has_developer_signal


def categorize_candidate(candidate: RawCandidate) -> str:
    """Assign a broad category from candidate metadata/signals."""
    metadata_blob = " ".join(str(value) for value in candidate.metadata.values())
    if has_developer_signal(metadata_blob):
        return "developer_tooling"
    if any(signal.value.startswith("recent_funding") for signal in candidate.signals):
        return "funded"
    return "general_b2b"
