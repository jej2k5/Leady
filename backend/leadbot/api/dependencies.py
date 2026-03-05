"""FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from .auth.authy_setup import auth_manager


def require_auth(authorization: str | None = Header(default=None)) -> dict:
    """Require valid Authy JWT from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    payload = auth_manager.verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload


def require_admin(payload: dict = Depends(require_auth)) -> dict:
    """Require admin role in JWT payload."""
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return payload
