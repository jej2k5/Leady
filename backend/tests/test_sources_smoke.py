from __future__ import annotations

import pytest

from leadbot.sources import funding_news, github_signals, hiring_signals


def test_sources_smoke_offline_builders() -> None:
    funded = funding_news.fetch_candidates([{"company_name": "Acme", "url": "https://x", "text": "Raised seed round"}])
    github = github_signals.fetch_candidates([{"company_name": "Acme", "url": "https://repo", "stars": 42}])
    hiring = hiring_signals.fetch_candidates([{"company_name": "Acme", "url": "https://jobs", "description": "API developer role"}])
    assert funded and github and hiring


@pytest.mark.network
def test_sources_network_smoke_placeholder() -> None:
    pytest.skip("Network smoke tests are opt-in and intentionally skipped in default test runs")
