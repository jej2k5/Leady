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


def test_register_creates_local_user_and_allows_login(client) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "new-user@example.com",
            "username": "new-user",
            "password": "secret123",
            "name": "New User",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token"]
    assert payload["user"]["email"] == "new-user@example.com"
    assert payload["user"]["name"] == "New User"

    login = client.post(
        "/api/auth/login",
        json={"username": "new-user", "password": "secret123"},
    )
    assert login.status_code == 200
    assert login.json()["token"]


def test_register_rejects_short_password(client) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "email": "short-pass@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 422
    assert "at least 8 characters" in response.json()["detail"]


def test_register_rejects_duplicate_email(client) -> None:
    email_conflict = client.post(
        "/api/auth/register",
        json={
            "email": "user@example.com",
            "username": "fresh-username",
            "password": "secret123",
        },
    )
    assert email_conflict.status_code == 409
    assert "email" in email_conflict.json()["detail"].lower()

    username_conflict = client.post(
        "/api/auth/register",
        json={
            "email": "brand-new@example.com",
            "username": "tester@example.com",
            "password": "secret123",
        },
    )
    assert username_conflict.status_code == 409
    assert "username" in username_conflict.json()["detail"].lower()


def test_protected_route_requires_bearer(client) -> None:
    response = client.get("/api/companies")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"
