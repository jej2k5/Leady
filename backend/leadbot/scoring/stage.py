"""Stage inference helpers for candidate evaluation."""

from __future__ import annotations

import re

from ..db.models import RawCandidate, SignalType


_SERIES_STAGE_PATTERNS: list[tuple[str, str]] = [
    (r"\bseries\s*c\b|\bseries[-_\s]?c\+\b|\blate[\s-]stage\b", "series_c"),
    (r"\bseries\s*b\b|\bgrowth\s+round\b|\bscale[-\s]?up\b", "series_b"),
    (r"\bseries\s*a\b|\bseed\s+round\b|\bpre[-\s]?series\s*a\b", "series_a"),
]


def _metadata_text(candidate: RawCandidate) -> str:
    values = [str(value) for value in candidate.metadata.values() if value is not None]
    return " ".join(values).lower()


def infer_stage(candidate: RawCandidate) -> str:
    """Infer fundraising stage from candidate signals and source text."""
    combined = " ".join(
        [
            candidate.source_url or "",
            _metadata_text(candidate),
            " ".join(signal.value for signal in candidate.signals),
        ]
    ).lower()

    for pattern, stage in _SERIES_STAGE_PATTERNS:
        if re.search(pattern, combined):
            return stage

    signal_types = {signal.signal_type for signal in candidate.signals}
    if SignalType.funding in signal_types and SignalType.hiring in signal_types:
        return "series_b"
    if SignalType.funding in signal_types:
        return "series_a"

    return "unknown"

