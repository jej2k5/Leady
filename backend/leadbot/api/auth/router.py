"""Authentication API routes using Authy."""

from __future__ import annotations

from typing import Any
import inspect

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
import requests

from ...db import queries
from ...config import get_settings
from ...db.session import get_connection
from ..dependencies import require_auth
from .authy_setup import auth_manager, mint_backend_jwt

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LocalLoginRequest(BaseModel):
    username: str
    password: str


class GoogleExchangeRequest(BaseModel):
    id_token: str | None = None
    access_token: str | None = None


def _google_tokeninfo_request(url: str, params: dict[str, str]) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=8)
    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Google token validation failed")
    return dict(response.json())


def _validate_google_identity(payload: GoogleExchangeRequest) -> dict[str, Any]:
    settings = get_settings()
    google_client_id = settings.auth.google_client_id
    if not google_client_id:
        raise HTTPException(status_code=400, detail="Google OAuth is not configured")

    if payload.id_token:
        tokeninfo = _google_tokeninfo_request(
            "https://oauth2.googleapis.com/tokeninfo",
            {"id_token": payload.id_token},
        )
    elif payload.access_token:
        tokeninfo = _google_tokeninfo_request(
            "https://www.googleapis.com/oauth2/v3/tokeninfo",
            {"access_token": payload.access_token},
        )
    else:
        raise HTTPException(status_code=400, detail="Missing Google id_token or access_token")

    aud = tokeninfo.get("aud")
    if aud != google_client_id:
        raise HTTPException(status_code=401, detail="Google token audience mismatch")

    email = tokeninfo.get("email")
    sub = tokeninfo.get("sub")
    if not email or not sub:
        raise HTTPException(status_code=401, detail="Google token missing required identity claims")

    return {
        "id": str(sub),
        "sub": str(sub),
        "email": str(email),
        "name": tokeninfo.get("name") or str(email).split("@", 1)[0],
        "role": "viewer",
    }


async def _authenticate(provider: str, data: dict[str, Any]) -> dict[str, Any]:
    result = auth_manager.authenticate(provider, data)
    if inspect.isawaitable(result):
        result = await result
    return dict(result)


@router.post("/login")
async def login(payload: LocalLoginRequest) -> dict[str, Any]:
    try:
        result = await _authenticate(
            "local",
            {
                "username": payload.username,
                "password": payload.password,
            },
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    token = str(result.get("token", ""))
    user = result.get("user") or {}
    return {"token": token, "user": user}


@router.get("/google")
async def google_auth_url() -> dict[str, str]:
    try:
        result = await _authenticate("google", {"action": "get_auth_url"})
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    auth_url = result.get("auth_url")
    if not auth_url:
        raise HTTPException(status_code=400, detail="Google auth URL unavailable")
    return {"auth_url": str(auth_url)}


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    code_verifier: str = Query(...),
) -> dict[str, Any]:
    try:
        result = await _authenticate(
            "google",
            {
                "action": "callback",
                "code": code,
                "state": state,
                "code_verifier": code_verifier,
            },
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    token = str(result.get("token", ""))
    user = result.get("user") or {}
    email = user.get("email")
    if email:
        with get_connection() as conn:
            queries.upsert_oauth_user(
                conn,
                email=str(email),
                name=user.get("name"),
                provider="google",
                google_sub=user.get("sub"),
            )

    return {"token": token, "user": user}


@router.post("/google/exchange")
async def google_exchange(payload: GoogleExchangeRequest) -> dict[str, Any]:
    try:
        user = _validate_google_identity(payload)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail="Unable to validate Google identity") from exc

    with get_connection() as conn:
        queries.upsert_oauth_user(
            conn,
            email=user["email"],
            name=user.get("name"),
            provider="google",
            google_sub=user.get("sub"),
        )

    try:
        token = mint_backend_jwt(user)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail="Unable to mint backend JWT") from exc

    return {"token": token, "user": user}


@router.get("/me")
def me(payload: dict = Depends(require_auth)) -> dict[str, Any]:
    return payload


@router.post("/logout")
def logout(_: dict = Depends(require_auth)) -> dict[str, bool]:
    return {"success": True}
