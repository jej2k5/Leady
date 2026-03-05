from __future__ import annotations

from fastapi.testclient import TestClient

from leadbot.api.app import app


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


def test_global_exception_handler_returns_500_and_logs(monkeypatch) -> None:
    called: dict[str, str] = {}

    def fake_exception(message: str, method: str, path: str) -> None:
        called["message"] = message
        called["method"] = method
        called["path"] = path

    from leadbot.api import app as app_module

    monkeypatch.setattr(app_module.logger, "exception", fake_exception)

    if not any(getattr(route, "path", None) == "/__test-error" for route in app.routes):
        @app.get("/__test-error")
        def _test_error() -> None:
            raise RuntimeError("boom")

    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/__test-error")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    assert called["message"] == "Unhandled server error on %s %s"
    assert called["method"] == "GET"
    assert called["path"] == "/__test-error"


def test_pipeline_start_kicks_off_run(client, auth_headers) -> None:
    response = client.post('/api/pipeline/start', headers=auth_headers, json={})
    assert response.status_code == 202
    payload = response.json()
    assert isinstance(payload['run_id'], int)

    runs = client.get('/api/runs', headers=auth_headers)
    assert runs.status_code == 200
    assert any(run['run_id'] == payload['run_id'] for run in runs.json())


def test_run_stream_route_returns_event_stream(client, auth_headers) -> None:
    created = client.post('/api/runs', headers=auth_headers, json={'status': 'completed'})
    assert created.status_code == 201
    run_id = created.json()['run_id']

    with client.stream('GET', f'/api/runs/{run_id}/stream', headers=auth_headers) as response:
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('text/event-stream')
        first_line = next(response.iter_lines())

    assert first_line.startswith('data: Status completed.')


def test_run_stream_supports_access_token_query_param(client, auth_headers) -> None:
    created = client.post('/api/runs', headers=auth_headers, json={'status': 'completed'})
    assert created.status_code == 201
    run_id = created.json()['run_id']
    token = auth_headers['Authorization'].removeprefix('Bearer ')

    with client.stream('GET', f'/api/runs/{run_id}/stream?access_token={token}') as response:
        assert response.status_code == 200
        assert response.headers['content-type'].startswith('text/event-stream')
