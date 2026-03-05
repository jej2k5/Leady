"""Discovery-stage parsing for early filtering."""

from __future__ import annotations

import re
from dataclasses import dataclass

_ACCEPT_STAGE_PATTERNS: dict[str, re.Pattern[str]] = {
    "series_c": re.compile(r"\bseries[-_\s]?c\b|\bseries[-_\s]?c\+\b", re.IGNORECASE),
    "series_b": re.compile(r"\bseries[-_\s]?b\b", re.IGNORECASE),
    "series_a": re.compile(r"\bseries[-_\s]?a\b", re.IGNORECASE),
}
_REJECT_STAGE_PATTERN = re.compile(r"\bpre[-_\s]?seed\b|\bseed\b", re.IGNORECASE)


@dataclass(slots=True)
class StageDecision:
    accepted: bool
    stage: str | None
    rejection_reason: str | None = None


def parse_stage(text_blobs: list[str]) -> StageDecision:
    corpus = " ".join(blob for blob in text_blobs if blob)

    if _REJECT_STAGE_PATTERN.search(corpus):
        return StageDecision(accepted=False, stage=None, rejection_reason="seed_or_pre_seed")

    for stage, pattern in _ACCEPT_STAGE_PATTERNS.items():
        if pattern.search(corpus):
            return StageDecision(accepted=True, stage=stage)

    return StageDecision(accepted=True, stage=None)
