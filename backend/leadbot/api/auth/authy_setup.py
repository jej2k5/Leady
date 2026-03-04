"""Authy-backed authentication manager wiring."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from .authy_compat import AuthManager, GoogleProvider, GoogleProviderConfig, LocalProvider, LocalProviderConfig
from pydantic import BaseModel

from ...config import get_settings
from ...db import queries
from ...db.session import get_connection


class LoginResult(BaseModel):
    """Normalized payload returned from auth endpoints."""

    token: str
    user: dict[str, Any]


async def find_local_user(username: str) -> dict[str, str] | None:
    """Look up local user from Leady users table by username/email."""
    with get_connection() as conn:
        user = queries.get_user_by_username(conn, username)
    if not user:
        return None
    password_hash = user.get("password_hash")
    if not password_hash:
        return None
    return {
        "id": str(user["id"]),
        "email": str(user["email"]),
        "name": str(user.get("name") or ""),
        "password_hash": str(password_hash),
    }


def build_auth_manager() -> AuthManager:
    settings = get_settings()
    manager = AuthManager(jwt_secret=settings.auth.jwt_secret)

    manager.register(
        LocalProvider(
            LocalProviderConfig(
                jwt_secret=settings.auth.jwt_secret,
                token_ttl=settings.auth.jwt_ttl_seconds,
            ),
            find_local_user,
        )
    )

    if settings.auth.google_client_id and settings.auth.google_client_secret:
        manager.register(
            GoogleProvider(
                GoogleProviderConfig(
                    client_id=settings.auth.google_client_id,
                    client_secret=settings.auth.google_client_secret,
                    redirect_uri=settings.auth.google_redirect_uri,
                    jwt_secret=settings.auth.jwt_secret,
                )
            )
        )

    return manager


@lru_cache(maxsize=1)
def get_auth_manager() -> AuthManager:
    return build_auth_manager()


# singleton for direct imports in dependencies/routes
auth_manager = get_auth_manager()
