from __future__ import annotations

from leadbot.db.queries import list_discovery_candidates
from leadbot.db.session import get_connection
from leadbot.discovery.orchestrator import discover_seed_data, emit_top_unseeded_source_seed_data


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

    with get_connection() as conn:
        persisted = list_discovery_candidates(conn, status="unseeded")

    assert len(persisted) >= 3


def test_emit_top_unseeded_source_seed_data_groups_and_marks_seeded() -> None:
    discover_seed_data(
        {
            "funding": {
                "rows": [
                    {
                        "company": "Delta",
                        "link": "https://news.example.com/delta",
                        "summary": "Delta raised Series A for AI infrastructure platform in US",
                    }
                ]
            },
            "hiring": {
                "rows": [
                    {
                        "company": "Delta",
                        "link": "https://jobs.example.com/delta",
                        "text": "Hiring platform engineering and DevOps roles",
                    }
                ]
            },
            "github": {
                "rows": [
                    {
                        "org_name": "Delta",
                        "repo_url": "https://github.com/delta/core",
                        "stars": 50,
                    }
                ]
            },
        }
    )

    selected = emit_top_unseeded_source_seed_data(limit_per_source=1)

    assert set(selected.keys()) == {"funding", "hiring", "github"}
    assert len(selected["funding"]) == 1
    assert len(selected["hiring"]) == 1
    assert len(selected["github"]) == 1
    assert selected["github"][0]["stars"] >= 0

    with get_connection() as conn:
        persisted = list_discovery_candidates(conn, status="seeded")

    assert any(
        any(
            isinstance(item, dict)
            and item.get("source_type") == "selector"
            and isinstance(item.get("payload"), dict)
            and item["payload"].get("allowed_for_seeding") is True
            for item in candidate.get("evidence") or []
        )
        for candidate in persisted
    )


def test_emit_top_unseeded_source_seed_data_rejects_seed_stage() -> None:
    discover_seed_data(
        {
            "funding": {
                "rows": [
                    {
                        "company": "Seedly",
                        "link": "https://news.example.com/seedly",
                        "summary": "Seedly raised Seed for security operations automation",
                    }
                ]
            }
        }
    )

    selected = emit_top_unseeded_source_seed_data(limit_per_source=1)

    assert selected == {"funding": [], "hiring": [], "github": []}
