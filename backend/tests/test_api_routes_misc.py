from __future__ import annotations


def test_runs_contacts_stats_routes(client, auth_headers) -> None:
    create_run = client.post("/api/runs", headers=auth_headers, json={"status": "running"})
    assert create_run.status_code == 201
    run_id = create_run.json()["run_id"]

    patch = client.patch(f"/api/runs/{run_id}", headers=auth_headers, json={"status": "completed"})
    assert patch.status_code == 200

    company = client.post(
        "/api/companies",
        headers=auth_headers,
        json={"run_id": run_id, "name": "Acme", "domain": "acme.io", "score": 60},
    ).json()
    contact = client.post(
        "/api/contacts",
        headers=auth_headers,
        json={
            "company_id": company["id"],
            "full_name": "Ada Lovelace",
            "contact_type": "email",
            "contact_value": "ada@acme.io",
            "is_primary": True,
        },
    )
    assert contact.status_code == 201

    contacts = client.get("/api/contacts", headers=auth_headers, params={"company_id": company["id"]})
    assert contacts.status_code == 200
    assert contacts.json()[0]["full_name"] == "Ada Lovelace"

    overview = client.get("/api/stats/overview")
    assert overview.status_code == 200
    assert overview.json()["completed_runs"] == 1
