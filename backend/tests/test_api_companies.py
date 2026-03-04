from __future__ import annotations


def test_create_and_list_companies(client, auth_headers) -> None:
    payload = {"run_id": 1, "name": "Acme", "domain": "acme.io", "industry": "SaaS", "score": 88.5}
    create = client.post("/api/companies", headers=auth_headers, json=payload)
    assert create.status_code == 201
    company_id = create.json()["id"]

    listing = client.get("/api/companies", headers=auth_headers)
    assert listing.status_code == 200
    assert listing.json()[0]["id"] == company_id

    fetched = client.get(f"/api/companies/{company_id}", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Acme"


def test_search_companies(client, auth_headers) -> None:
    client.post("/api/companies", headers=auth_headers, json={"run_id": 1, "name": "Zeta Labs", "domain": "zeta.dev", "score": 50})
    client.post("/api/companies", headers=auth_headers, json={"run_id": 1, "name": "Other", "domain": "other.com", "score": 20})

    response = client.get("/api/companies", headers=auth_headers, params={"q": "zeta"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["domain"] == "zeta.dev"
