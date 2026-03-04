"""Authentication API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr

from ..dependencies import require_auth
from .authy_setup import AuthUser, LoginResult, get_auth_manager

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LocalLoginRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class GoogleLoginRequest(BaseModel):
    google_token: str
    email: EmailStr | None = None
    full_name: str | None = None


@router.post("/login", response_model=LoginResult)
def login(payload: LocalLoginRequest) -> LoginResult:
    manager = get_auth_manager()
    try:
        return manager.login_local(
            email=str(payload.email),
            password=payload.password,
            full_name=payload.full_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/google", response_model=LoginResult)
def google_login(payload: GoogleLoginRequest) -> LoginResult:
    manager = get_auth_manager()
    try:
        return manager.login_google(
            google_token=payload.google_token,
            email=str(payload.email) if payload.email else None,
            full_name=payload.full_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/google/callback", response_model=LoginResult)
def google_callback(
    token: str = Query(..., alias="token"),
    email: EmailStr | None = Query(default=None),
    name: str | None = Query(default=None),
) -> LoginResult:
    manager = get_auth_manager()
    try:
        return manager.login_google(google_token=token, email=str(email) if email else None, full_name=name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.get("/me", response_model=AuthUser)
def me(current_user: AuthUser = Depends(require_auth)) -> AuthUser:
    return current_user


@router.post("/logout")
def logout(_: AuthUser = Depends(require_auth)) -> dict[str, str]:
    return {"detail": "Logged out"}
