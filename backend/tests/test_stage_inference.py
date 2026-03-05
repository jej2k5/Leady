from __future__ import annotations

import csv
from io import StringIO

from leadbot.db.models import RawCandidate, Signal, SignalType, SourceType
from leadbot.scoring.engine import evaluate_candidate
from leadbot.scoring.stage import infer_stage


def test_infer_stage_detects_series_b_from_funding_text() -> None:
    candidate = RawCandidate(
        company_name="Signal Co",
        source_type=SourceType.website,
        source_url="https://news.example.com/signal-co-funding",
        signals=[Signal(company_id=0, signal_type=SignalType.funding, value="recent_funding_mentioned", confidence=0.8)],
        metadata={"funding_text": "Signal Co announced a Series B to accelerate hiring."},
    )

    assert infer_stage(candidate) == "series_b"
    assert evaluate_candidate(candidate)["stage"] == "series_b"


def test_pipeline_persists_stage_and_outreach_includes_known_stage(client, auth_headers) -> None:
    response = client.post(
        "/api/pipeline/start",
        headers=auth_headers,
        json={
            "sources": "funding",
            "include_unknown_stage": False,
            "source_seed_data": {
                "funding": [
                    {
                        "company_name": "Series Stage Co",
                        "url": "https://news.example.com/series-stage-co",
                        "text": "Series Stage Co just closed a Series B round and plans to expand engineering.",
                    }
                ]
            },
        },
    )
    assert response.status_code == 202
    run_id = response.json()["run_id"]

    companies_resp = client.get("/api/companies", headers=auth_headers, params={"run_id": run_id})
    assert companies_resp.status_code == 200
    companies = companies_resp.json()
    assert companies
    assert companies[0]["metadata"]["stage"] != "unknown"

    outreach = client.get(
        "/api/export/outreach_queue.csv",
        headers=auth_headers,
        params={"run_id": run_id, "include_unknown_stage": False},
    )
    assert outreach.status_code == 200
    rows = list(csv.DictReader(StringIO(outreach.text)))
    assert rows
    assert rows[0]["company_name"] == "Series Stage Co"
    assert rows[0]["stage"] == "series_b"
