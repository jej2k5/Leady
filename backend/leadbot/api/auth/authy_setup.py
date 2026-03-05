"""Authy-backed authentication manager wiring."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
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


def mint_backend_jwt(user: dict[str, Any]) -> str:
    """Mint a backend JWT that is verifiable by ``require_auth``.

    The token is signed with the same secret configured for AuthManager.
    """

    settings = get_settings()
    now = int(time.time())
    payload = {
        "sub": str(user.get("id") or user.get("sub") or user.get("email") or "google-user"),
        "email": str(user.get("email") or ""),
        "name": user.get("name"),
        "role": str(user.get("role") or "viewer"),
        "provider": "google",
        "iat": now,
        "exp": now + int(settings.auth.jwt_ttl_seconds),
    }

    google_sub = user.get("sub")
    if google_sub:
        payload["google_sub"] = str(google_sub)

    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("utf-8")
    body = body.rstrip("=")
    signature = base64.urlsafe_b64encode(
        hmac.new(settings.auth.jwt_secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")
    token = f"{body}.{signature.rstrip('=')}"

    if not auth_manager.verify_token(token):
        raise ValueError("Unable to mint a valid backend JWT")

    return token
