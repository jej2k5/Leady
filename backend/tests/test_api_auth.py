from __future__ import annotations

import sqlite3


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


def test_register_rejects_username_only_payload(client) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "username": "not-an-email",
            "password": "secret123",
        },
    )

    assert response.status_code == 422
    assert "email is required" in response.json()["detail"].lower()


def test_register_returns_conflict_on_integrity_error(client, monkeypatch) -> None:
    from leadbot.api.auth import router

    def _raise_integrity_error(*args, **kwargs):
        raise sqlite3.IntegrityError("UNIQUE constraint failed: users.email")

    monkeypatch.setattr(router.queries, "create_user", _raise_integrity_error)

    response = client.post(
        "/api/auth/register",
        json={
            "email": "integrity-check@example.com",
            "username": "integrity-check",
            "password": "secret123",
        },
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


def test_protected_route_requires_bearer(client) -> None:
    response = client.get("/api/companies")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"


def test_login_accepts_object_auth_result(client, monkeypatch) -> None:
    from leadbot.api.auth import router

    class AuthResult:
        def __init__(self) -> None:
            self.token = "token-from-object"
            self.user = {"email": "user@example.com"}

    def _return_object_result(*args, **kwargs):
        return AuthResult()

    monkeypatch.setattr(router.auth_manager, "authenticate", _return_object_result)

    response = client.post(
        "/api/auth/login",
        json={"username": "user@example.com", "password": "superpass123"},
    )

    assert response.status_code == 200
    assert response.json()["token"] == "token-from-object"
    assert response.json()["user"]["email"] == "user@example.com"
