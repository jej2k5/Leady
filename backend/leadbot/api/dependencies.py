"""FastAPI dependency helpers for auth and authorization."""

from __future__ import annotations

import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .auth.authy_setup import AuthUser, get_auth_manager

bearer_scheme = HTTPBearer(auto_error=False)


def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthUser:
    """Require a valid bearer token and return authenticated user context."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_auth_manager().authenticate_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(user: AuthUser = Depends(require_auth)) -> AuthUser:
    """Require authenticated user to be an admin."""
    raw = os.getenv("LEADBOT_ADMIN_EMAILS", "")
    admins = {item.strip().lower() for item in raw.split(",") if item.strip()}
    if admins and str(user.email).lower() not in admins:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user
