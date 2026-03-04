from __future__ import annotations


def test_auth_login_and_me(client) -> None:
    login = client.post(
        "/api/auth/login",
        json={"username": "user@example.com", "password": "superpass123"},
    )
    assert login.status_code == 200
    token = login.json()["token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"


def test_auth_rejects_short_password(client) -> None:
    response = client.post("/api/auth/login", json={"username": "x@example.com", "password": "short"})
    assert response.status_code == 401


def test_protected_route_requires_bearer(client) -> None:
    response = client.get("/api/companies")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"
