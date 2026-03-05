from __future__ import annotations

from datetime import UTC, datetime

from leadbot.discovery.providers.github_orgs import fetch_github_org_signals
from leadbot.sources.github_signals import fetch_candidates


class _FakeResponse:
    def __init__(self, status_code: int, payload: object, headers: dict[str, str] | None = None) -> None:
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self) -> object:
        return self._payload


class _FakeSession:
    def __init__(self, responses: dict[str, _FakeResponse]) -> None:
        self._responses = responses

    def get(self, url: str, *, headers: dict[str, str], timeout: float) -> _FakeResponse:  # noqa: ARG002
        return self._responses[url]


def test_fetch_github_org_signals_maps_org_repos_into_seed_rows(monkeypatch, tmp_path) -> None:
    now = datetime.now(UTC).isoformat()
    responses = {
        "https://api.github.com/orgs/acme": _FakeResponse(
            200,
            {
                "login": "acme",
                "name": "Acme Inc",
                "html_url": "https://github.com/acme",
                "description": "Cloud platform",
                "public_repos": 2,
            },
        ),
        "https://api.github.com/orgs/acme/repos?sort=updated&per_page=5&type=public": _FakeResponse(
            200,
            [
                {
                    "name": "secure-api",
                    "html_url": "https://github.com/acme/secure-api",
                    "stargazers_count": 50,
                    "pushed_at": now,
                    "description": "Security gateway",
                    "topics": ["security", "api"],
                },
                {
                    "name": "deploy",
                    "html_url": "https://github.com/acme/deploy",
                    "stargazers_count": 15,
                    "pushed_at": now,
                    "description": "Deployment tools",
                    "topics": ["devops", "integration"],
                },
            ],
        ),
    }

    monkeypatch.setattr("leadbot.discovery.providers.github_orgs.requests.Session", lambda: _FakeSession(responses))

    rows = fetch_github_org_signals(
        {
            "orgs": ["acme"],
            "cache_path": str(tmp_path / "github_cache.json"),
            "top_repos": 5,
            "min_aggregate_stars": 10,
        }
    )

    assert len(rows) == 2
    assert rows[0]["company_name"] == "Acme Inc"
    assert rows[0]["url"].startswith("https://github.com/acme/")
    assert isinstance(rows[0]["stars"], int)
    assert rows[0]["aggregate_stars"] == 65
    assert rows[0]["recent_push_count"] == 2
    assert rows[0]["topic_security_count"] == 1
    assert rows[0]["topic_devops_count"] == 1
    assert rows[0]["topic_integration_count"] == 2


def test_fetch_github_org_signals_rows_work_with_github_candidate_mapping(monkeypatch, tmp_path) -> None:
    responses = {
        "https://api.github.com/orgs/empty": _FakeResponse(
            200,
            {
                "login": "empty",
                "name": "Empty Org",
                "html_url": "https://github.com/empty",
                "description": "",
                "public_repos": 0,
            },
        ),
        "https://api.github.com/orgs/empty/repos?sort=updated&per_page=5&type=public": _FakeResponse(200, []),
        "https://api.github.com/orgs/shipit": _FakeResponse(
            200,
            {
                "login": "shipit",
                "name": "ShipIt",
                "html_url": "https://github.com/shipit",
                "description": "Integrations",
                "public_repos": 1,
            },
        ),
        "https://api.github.com/orgs/shipit/repos?sort=updated&per_page=5&type=public": _FakeResponse(
            200,
            [
                {
                    "name": "connector",
                    "html_url": "https://github.com/shipit/connector",
                    "stargazers_count": 9,
                    "pushed_at": "2026-01-01T00:00:00Z",
                    "description": "Connector",
                    "topics": ["integration"],
                }
            ],
        ),
    }

    monkeypatch.setattr("leadbot.discovery.providers.github_orgs.requests.Session", lambda: _FakeSession(responses))

    rows = fetch_github_org_signals(
        {
            "orgs": ["empty", "shipit"],
            "cache_path": str(tmp_path / "github_cache.json"),
            "top_repos": 5,
            "min_aggregate_stars": 1,
        }
    )
    assert len(rows) == 1

    seed_payload = [{"company_name": row["company_name"], "url": row["url"], "stars": row["stars"]} for row in rows]
    candidates = fetch_candidates(seed_payload)

    assert len(candidates) == 1
    assert candidates[0].company_name == "ShipIt"
    assert candidates[0].source_url == "https://github.com/shipit/connector"
    assert candidates[0].metadata["github_stars"] == 9
