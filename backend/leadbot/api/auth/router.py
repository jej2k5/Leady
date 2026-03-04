"""Authentication API routes using Authy."""

from __future__ import annotations

from typing import Any
import inspect

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ...db import queries
from ...db.session import get_connection
from ..dependencies import require_auth
from .authy_setup import auth_manager

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LocalLoginRequest(BaseModel):
    username: str
    password: str


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


@router.get("/me")
def me(payload: dict = Depends(require_auth)) -> dict[str, Any]:
    return payload


@router.post("/logout")
def logout(_: dict = Depends(require_auth)) -> dict[str, bool]:
    return {"success": True}
