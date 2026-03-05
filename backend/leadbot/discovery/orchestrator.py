"""Discovery orchestrator for seed data used by the pipeline."""

from __future__ import annotations

from typing import Any

from ..pipeline.orchestrator import SourceSeedData
from .providers.funding_web import fetch_funding_articles
from .providers.github_orgs import fetch_github_org_signals
from .providers.job_boards import fetch_job_posts


def discover_seed_data(query_config: dict[str, Any] | None = None) -> SourceSeedData:
    """Collect normalized seed rows from discovery providers.

    The output shape matches ``run_pipeline_for_run(..., source_seed_data=...)`` expectations.
    """
    config = query_config or {}

    funding_cfg = config.get("funding") if isinstance(config.get("funding"), dict) else {}
    hiring_cfg = config.get("hiring") if isinstance(config.get("hiring"), dict) else {}
    github_cfg = config.get("github") if isinstance(config.get("github"), dict) else {}

    return {
        "funding": fetch_funding_articles(funding_cfg),
        "hiring": fetch_job_posts(hiring_cfg),
        "github": fetch_github_org_signals(github_cfg),
    }
