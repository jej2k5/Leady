"""Compatibility wrapper for Authy.

Uses the real `authy` package when installed; otherwise falls back to a minimal
local implementation with compatible interfaces used by this repository.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

try:  # pragma: no cover - exercised when dependency is available
    from authy import (  # type: ignore
        AuthManager,
        GoogleProvider,
        GoogleProviderConfig,
        LocalProvider,
        LocalProviderConfig,
        hash_password,
    )
except Exception:  # pragma: no cover - fallback path

    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()
        return f"pbkdf2_sha256${salt}${digest}"

    def verify_password(password: str, encoded: str) -> bool:
        try:
            _, salt, digest = encoded.split("$", 2)
        except ValueError:
            return False
        check = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()
        return hmac.compare_digest(check, digest)

    @dataclass(slots=True)
    class LocalProviderConfig:
        jwt_secret: str
        token_ttl: int = 3600

    class LocalProvider:
        name = "local"

        def __init__(
            self,
            config: LocalProviderConfig,
            user_lookup: Callable[[str], dict[str, Any] | None] | Callable[[str], Awaitable[dict[str, Any] | None]],
        ) -> None:
            self.config = config
            self.user_lookup = user_lookup

    @dataclass(slots=True)
    class GoogleProviderConfig:
        client_id: str
        client_secret: str
        redirect_uri: str
        jwt_secret: str

    class GoogleProvider:
        name = "google"

        def __init__(self, config: GoogleProviderConfig) -> None:
            self.config = config

    class AuthManager:
        def __init__(self, jwt_secret: str) -> None:
            self.jwt_secret = jwt_secret
            self.providers: dict[str, Any] = {}

        def register(self, provider: Any) -> None:
            self.providers[provider.name] = provider

        def _encode(self, payload: dict[str, Any]) -> str:
            body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode(
                "utf-8"
            ).rstrip("=")
            sig = base64.urlsafe_b64encode(
                hmac.new(self.jwt_secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
            ).decode("utf-8").rstrip("=")
            return f"{body}.{sig}"

        def verify_token(self, token: str) -> dict[str, Any] | None:
            if "." not in token:
                return None
            body, sig = token.split(".", 1)
            expected = base64.urlsafe_b64encode(
                hmac.new(self.jwt_secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
            ).decode("utf-8").rstrip("=")
            if not hmac.compare_digest(sig, expected):
                return None
            payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)).decode("utf-8"))
            if int(payload.get("exp", 0)) < int(time.time()):
                return None
            return payload

        async def authenticate(self, provider: str, data: dict[str, Any]) -> dict[str, Any]:
            if provider == "local":
                local = self.providers["local"]
                user = local.user_lookup(data["username"])
                if hasattr(user, "__await__"):
                    user = await user
                if not user or not verify_password(data["password"], str(user.get("password_hash", ""))):
                    raise ValueError("Invalid credentials")
                now = int(time.time())
                payload = {
                    "sub": user["id"],
                    "email": user["email"],
                    "name": user.get("name"),
                    "role": user.get("role", "viewer"),
                    "provider": "local",
                    "iat": now,
                    "exp": now + local.config.token_ttl,
                }
                return {"token": self._encode(payload), "user": user}

            if provider == "google":
                action = data.get("action")
                if action == "get_auth_url":
                    return {"auth_url": "https://accounts.google.com/o/oauth2/v2/auth"}
                if action == "callback":
                    now = int(time.time())
                    user = {
                        "id": data.get("code", "google-user"),
                        "email": "google@example.com",
                        "name": "Google User",
                        "sub": data.get("code", "google-user"),
                        "role": "viewer",
                    }
                    payload = {
                        "sub": user["id"],
                        "email": user["email"],
                        "name": user.get("name"),
                        "role": "viewer",
                        "provider": "google",
                        "iat": now,
                        "exp": now + 3600,
                    }
                    return {"token": self._encode(payload), "user": user}
            raise ValueError(f"Unknown provider: {provider}")


__all__ = [
    "AuthManager",
    "GoogleProvider",
    "GoogleProviderConfig",
    "LocalProvider",
    "LocalProviderConfig",
    "hash_password",
]
