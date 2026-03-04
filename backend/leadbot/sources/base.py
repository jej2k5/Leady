"""Source adapter abstractions and composition helpers."""

from __future__ import annotations

from collections.abc import Iterable, Protocol

from ..db.models import RawCandidate


class SourceAdapter(Protocol):
    """Protocol for source adapters that discover candidates."""

    def fetch_candidates(self) -> list[RawCandidate]:
        """Return discovered raw candidates."""


def gather_candidates(adapters: Iterable[SourceAdapter]) -> list[RawCandidate]:
    """Fetch and flatten candidates from multiple adapters."""
    discovered: list[RawCandidate] = []
    for adapter in adapters:
        discovered.extend(adapter.fetch_candidates())
    return discovered
