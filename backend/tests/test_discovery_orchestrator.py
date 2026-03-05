from __future__ import annotations

from leadbot.discovery.orchestrator import discover_seed_data


def test_discover_seed_data_returns_pipeline_shape() -> None:
    data = discover_seed_data(
        {
            "funding": {
                "rows": [
                    {
                        "company": "Acme",
                        "link": "https://news.example.com/acme",
                        "summary": "Acme raised Series A",
                        "published": "2026-01-01",
                    }
                ]
            },
            "hiring": {
                "rows": [
                    {
                        "company": "Beta",
                        "link": "https://jobs.example.com/beta",
                        "text": "Hiring backend engineer",
                        "posted": "2026-01-02",
                    }
                ]
            },
            "github": {
                "rows": [
                    {
                        "org_name": "Gamma",
                        "repo_url": "https://github.com/gamma/core",
                        "stars": "17",
                        "repos": "4",
                    }
                ]
            },
        }
    )

    assert set(data.keys()) == {"funding", "hiring", "github"}
    assert data["funding"][0]["company_name"] == "Acme"
    assert data["funding"][0]["source"] == "funding_web"
    assert data["hiring"][0]["description"] == "Hiring backend engineer"
    assert data["github"][0]["stars"] == 17
    assert data["github"][0]["repo_count"] == 4
