"""Model Context Protocol HTTP surface for Leady tools."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .middleware import MCPApiKeyMiddleware, enforce_write_gate
from .tools import TOOL_SCHEMAS, WRITE_TOOLS, execute_tool


class ToolCallRequest(BaseModel):
    name: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


def create_mcp_app() -> FastAPI:
    app = FastAPI(title="Leady MCP", version="0.1.0")
    app.add_middleware(MCPApiKeyMiddleware)

    @app.get("/")
    def root() -> dict[str, Any]:
        return {"name": "leady-mcp", "tools": len(TOOL_SCHEMAS)}

    @app.get("/tools")
    def list_tools() -> dict[str, Any]:
        return {"tools": TOOL_SCHEMAS}

    @app.post("/tools/call")
    def call_tool(payload: ToolCallRequest) -> dict[str, Any]:
        return _execute_tool(payload.name, payload.arguments)

    @app.post("/tools/{tool_name}")
    def call_tool_by_path(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        return _execute_tool(tool_name, arguments)

    return app


def _execute_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    try:
        enforce_write_gate(tool_name, WRITE_TOOLS)
        result = execute_tool(tool_name, arguments)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"tool": tool_name, "result": result}


mcp_app = create_mcp_app()
