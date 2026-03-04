"""MCP middleware for API-key auth and write gating."""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable

from fastapi import HTTPException, status
from fastapi.requests import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response


class MCPApiKeyMiddleware(BaseHTTPMiddleware):
    """Validate MCP API key when MCP_API_KEY is configured."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        configured_key = os.getenv("MCP_API_KEY", "").strip()
        if not configured_key:
            return await call_next(request)

        provided_key = request.headers.get("x-api-key", "").strip()
        authorization = request.headers.get("authorization", "").strip()
        if authorization.lower().startswith("bearer "):
            provided_key = authorization[7:].strip() or provided_key

        if provided_key != configured_key:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Invalid MCP API key"})

        return await call_next(request)


def writes_enabled() -> bool:
    return os.getenv("MCP_ALLOW_WRITES", "false").strip().lower() in {"1", "true", "yes", "on"}


def enforce_write_gate(tool_name: str, write_tools: set[str]) -> None:
    if tool_name in write_tools and not writes_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Writes are disabled. Set MCP_ALLOW_WRITES=true to enable write tools.",
        )
