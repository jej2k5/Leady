from __future__ import annotations

from leadbot.db.session import get_connection
from leadbot.jobs.discovery_pipeline_job import DiscoveryPipelineConfig, run_discovery_pipeline_job


def test_discovery_pipeline_job_persists_metadata(monkeypatch) -> None:
    discovered = {
        "funding": [
            {
                "company_name": "Acme",
                "url": "https://acme.io/raise",
                "text": "Acme raised to expand devops automation",
            }
        ],
        "hiring": [
            {
                "company_name": "Acme",
                "url": "https://acme.io/jobs",
                "description": "Hiring platform engineers",
            }
        ],
        "github": [],
    }

    monkeypatch.setattr(
        "leadbot.jobs.discovery_pipeline_job.discover_seed_data",
        lambda _cfg: discovered,
    )

    captured: dict[str, object] = {}

    def fake_run_pipeline_for_run(run_id: int, **kwargs) -> None:
        captured["run_id"] = run_id
        captured["seed_data"] = kwargs["source_seed_data"]

    monkeypatch.setattr(
        "leadbot.jobs.discovery_pipeline_job.run_pipeline_for_run",
        fake_run_pipeline_for_run,
    )

    result = run_discovery_pipeline_job(
        DiscoveryPipelineConfig(days=7, sources="funding,hiring", categories=["devops"], max_candidates=5)
    )

    assert isinstance(result["run_id"], int)
    assert result["seeded_count"] == 1
    assert captured["seed_data"]["funding"][0]["company_name"] == "Acme"

    with get_connection() as conn:
        row = conn.execute(
            "SELECT run_id, candidates_scanned, seeded_count, status FROM discovery_pipeline_job_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()

    assert row is not None
    assert int(row["run_id"]) == int(result["run_id"])
    assert int(row["candidates_scanned"]) >= 1
    assert int(row["seeded_count"]) == 1
    assert row["status"] == "completed"
