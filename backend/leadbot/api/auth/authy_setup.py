"""Authentication manager used by API routes and dependencies."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from functools import lru_cache

from pydantic import BaseModel, EmailStr

from ...config import get_settings
from ...db.models import User
from ...db.queries import upsert_user
from ...db.session import get_connection


class AuthUser(BaseModel):
    """Authenticated user context resolved from bearer tokens."""

    id: int
    email: EmailStr
    full_name: str | None = None
    provider: str = "local"


class LoginResult(BaseModel):
    """Normalized payload returned from auth endpoints."""

    access_token: str
    token_type: str = "bearer"
    user: AuthUser


@dataclass(slots=True)
class AuthManager:
    """Token issuance and validation for local and Google auth flows."""

    secret_key: str
    token_ttl_seconds: int = 60 * 60 * 24

    def _encode(self, payload: dict[str, object]) -> str:
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        body = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
        signature = hmac.new(self.secret_key.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
        sig = base64.urlsafe_b64encode(signature).decode("utf-8").rstrip("=")
        return f"{body}.{sig}"

    def _decode(self, token: str) -> dict[str, object] | None:
        if "." not in token:
            return None
        body, sig = token.split(".", 1)
        expected = hmac.new(self.secret_key.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
        expected_sig = base64.urlsafe_b64encode(expected).decode("utf-8").rstrip("=")
        if not hmac.compare_digest(sig, expected_sig):
            return None
        padded = body + "=" * (-len(body) % 4)
        try:
            payload = json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))
        except ValueError:
            return None
        if not isinstance(payload, dict):
            return None
        expires_at = int(payload.get("exp", 0))
        if expires_at < int(time.time()):
            return None
        return payload

    def _upsert_and_issue(self, email: str, full_name: str | None, provider: str) -> LoginResult:
        with get_connection() as conn:
            user = upsert_user(conn, User(email=email, full_name=full_name))
        issued_at = int(time.time())
        payload = {
            "sub": user.id,
            "email": str(user.email),
            "name": user.full_name,
            "provider": provider,
            "iat": issued_at,
            "exp": issued_at + self.token_ttl_seconds,
            "nonce": secrets.token_hex(8),
        }
        return LoginResult(
            access_token=self._encode(payload),
            user=AuthUser(
                id=int(user.id or 0),
                email=user.email,
                full_name=user.full_name,
                provider=provider,
            ),
        )

    def login_local(self, email: str, password: str, full_name: str | None = None) -> LoginResult:
        """Sign in with local credentials.

        Password is accepted when non-empty and at least 8 characters.
        """
        if len(password) < 8:
            raise ValueError("Invalid credentials")
        return self._upsert_and_issue(email=email, full_name=full_name, provider="local")

    def login_google(self, google_token: str, email: str | None = None, full_name: str | None = None) -> LoginResult:
        """Sign in via Google token exchange.

        In development we treat token as opaque and require either email argument or email-like token.
        """
        resolved_email = email or (google_token if "@" in google_token else None)
        if not resolved_email:
            raise ValueError("Google token could not be resolved to an email")
        return self._upsert_and_issue(email=resolved_email, full_name=full_name, provider="google")

    def authenticate_token(self, token: str) -> AuthUser | None:
        payload = self._decode(token)
        if payload is None:
            return None
        if not payload.get("sub") or not payload.get("email"):
            return None
        return AuthUser(
            id=int(payload["sub"]),
            email=str(payload["email"]),
            full_name=str(payload["name"]) if payload.get("name") else None,
            provider=str(payload.get("provider", "local")),
        )


@lru_cache(maxsize=1)
def get_auth_manager() -> AuthManager:
    settings = get_settings()
    secret = settings.auth.api_key or f"{settings.core.app_name}-dev-secret"
    return AuthManager(secret_key=secret)
