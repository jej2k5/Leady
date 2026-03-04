from __future__ import annotations

import csv
from io import StringIO

from leadbot.db.models import Company
from leadbot.exports.csv_export import build_outreach_queue_csv, build_raw_candidates_csv


def test_outreach_queue_excludes_unknown_stage_and_includes_ranking() -> None:
    companies = [
        Company(id=1, run_id=10, name="Known", score=80, metadata={"stage": "qualified"}),
        Company(id=2, run_id=10, name="Unknown", score=95, metadata={"stage": "unknown"}),
        Company(id=3, run_id=10, name="Missing", score=70, metadata={}),
    ]

    content = build_outreach_queue_csv(companies)
    rows = list(csv.DictReader(StringIO(content)))

    assert [row["company_name"] for row in rows] == ["Known"]
    assert rows[0]["score"] == "80.0"
    assert rows[0]["ranking"] == "2"


def test_raw_candidates_keeps_all_with_ranking() -> None:
    companies = [
        Company(id=1, run_id=10, name="Alpha", score=20, metadata={"stage": "unknown"}),
        Company(id=2, run_id=10, name="Beta", score=60, metadata={"stage": "outreach"}),
    ]

    content = build_raw_candidates_csv(companies)
    rows = list(csv.DictReader(StringIO(content)))

    assert [row["company_name"] for row in rows] == ["Beta", "Alpha"]
    assert [row["ranking"] for row in rows] == ["1", "2"]


def test_export_routes_and_pipeline_completion(client, auth_headers) -> None:
    run_id = client.post("/api/runs", headers=auth_headers, json={"status": "running"}).json()["run_id"]

    companies = [
        {"run_id": run_id, "name": "Ranked", "domain": "ranked.io", "score": 88, "metadata": {"stage": "qualified"}},
        {"run_id": run_id, "name": "Unknown", "domain": "unknown.io", "score": 99, "metadata": {"stage": "unknown"}},
    ]
    for payload in companies:
        resp = client.post("/api/companies", headers=auth_headers, json=payload)
        assert resp.status_code == 201

    outreach = client.get("/api/export/outreach_queue.csv", headers=auth_headers, params={"run_id": run_id})
    assert outreach.status_code == 200
    outreach_rows = list(csv.DictReader(StringIO(outreach.text)))
    assert [row["company_name"] for row in outreach_rows] == ["Ranked"]
    assert "score" in outreach_rows[0]
    assert "ranking" in outreach_rows[0]

    raw = client.get("/api/export/raw_candidates.csv", headers=auth_headers, params={"run_id": run_id})
    assert raw.status_code == 200
    raw_rows = list(csv.DictReader(StringIO(raw.text)))
    assert [row["company_name"] for row in raw_rows] == ["Unknown", "Ranked"]

    complete = client.post("/api/pipeline/complete", headers=auth_headers, json={"run_id": run_id})
    assert complete.status_code == 200
    body = complete.json()
    assert body["exports"]["outreach_queue"].endswith(f"run_id={run_id}")
    assert body["exports"]["raw_candidates"].endswith(f"run_id={run_id}")
