from __future__ import annotations

from collections.abc import Iterator

import pytest

from leadbot.api.auth.authy_setup import get_auth_manager
from leadbot.config import get_settings
from leadbot.db.schema import init_db


@pytest.fixture(autouse=True)
def isolated_sqlite_env(tmp_path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("LEADBOT_DB_PATH", str(db_path))
    get_settings.cache_clear()
    get_auth_manager.cache_clear()
    init_db(db_path).close()
    yield
    get_settings.cache_clear()
    get_auth_manager.cache_clear()


@pytest.fixture()
def client():
    pytest.importorskip("fastapi")
    pytest.importorskip("starlette")
    from fastapi.testclient import TestClient

    from leadbot.api.app import app

    return TestClient(app)


@pytest.fixture()
def auth_headers(client) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": "tester@example.com", "password": "secret123", "full_name": "Tester"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
