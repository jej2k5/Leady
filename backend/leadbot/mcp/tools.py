"""MCP tool schemas and database-backed handlers."""

from __future__ import annotations

import csv
import io
from collections.abc import Callable
from typing import Any

from ..db.models import Company, RunStatus
from ..db.queries import (
    create_run,
    get_company,
    list_companies,
    list_contacts_for_company,
    list_runs,
    list_signals_for_company,
    search_companies,
)
from ..db.session import get_connection

ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


_TOOL_DEFS: list[tuple[str, str, dict[str, Any]]] = [
    (
        "search_companies",
        "Search companies by name, domain, or industry.",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 1},
                "limit": {"type": "integer", "minimum": 1, "default": 20},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    ),
    (
        "get_company",
        "Fetch a company by ID.",
        {
            "type": "object",
            "properties": {"company_id": {"type": "integer", "minimum": 1}},
            "required": ["company_id"],
            "additionalProperties": False,
        },
    ),
    (
        "get_top_leads",
        "Get top scored companies.",
        {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "default": 10},
                "run_id": {"type": "integer", "minimum": 1},
            },
            "additionalProperties": False,
        },
    ),
    (
        "get_signals",
        "List signals associated with a company.",
        {
            "type": "object",
            "properties": {"company_id": {"type": "integer", "minimum": 1}},
            "required": ["company_id"],
            "additionalProperties": False,
        },
    ),
    (
        "get_contacts",
        "List contacts associated with a company.",
        {
            "type": "object",
            "properties": {"company_id": {"type": "integer", "minimum": 1}},
            "required": ["company_id"],
            "additionalProperties": False,
        },
    ),
    (
        "get_run_stats",
        "Fetch run summary stats.",
        {
            "type": "object",
            "properties": {"run_id": {"type": "integer", "minimum": 1}},
            "additionalProperties": False,
        },
    ),
    (
        "export_leads",
        "Export leads as CSV payload.",
        {
            "type": "object",
            "properties": {
                "run_id": {"type": "integer", "minimum": 1},
                "limit": {"type": "integer", "minimum": 1},
                "min_score": {"type": "number"},
            },
            "additionalProperties": False,
        },
    ),
    (
        "trigger_run",
        "Create a new lead run record.",
        {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer", "minimum": 1},
                "status": {"type": "string", "enum": [status.value for status in RunStatus]},
            },
            "additionalProperties": False,
        },
    ),
]

TOOL_SCHEMAS: list[dict[str, Any]] = []
for short_name, description, input_schema in _TOOL_DEFS:
    full_name = f"leady.{short_name}"
    TOOL_SCHEMAS.append({"name": full_name, "description": description, "input_schema": input_schema, "inputSchema": input_schema})


def _serialize_company(company: Company) -> dict[str, Any]:
    return company.model_dump(mode="json")


def handle_search_companies(arguments: dict[str, Any]) -> dict[str, Any]:
    query = str(arguments.get("query", "")).strip()
    limit = int(arguments.get("limit", 20))
    with get_connection() as conn:
        matches = search_companies(conn, query)
    return {"companies": [_serialize_company(company) for company in matches[:limit]]}


def handle_get_company(arguments: dict[str, Any]) -> dict[str, Any]:
    company_id = int(arguments["company_id"])
    with get_connection() as conn:
        company = get_company(conn, company_id)
    return {"company": _serialize_company(company)}


def handle_get_top_leads(arguments: dict[str, Any]) -> dict[str, Any]:
    limit = int(arguments.get("limit", 10))
    run_id = arguments.get("run_id")
    with get_connection() as conn:
        companies = list_companies(conn, run_id=int(run_id) if run_id is not None else None)
    ranked = sorted(companies, key=lambda item: (item.score, item.id or 0), reverse=True)
    return {"leads": [_serialize_company(company) for company in ranked[:limit]]}


def handle_get_signals(arguments: dict[str, Any]) -> dict[str, Any]:
    company_id = int(arguments["company_id"])
    with get_connection() as conn:
        signals = list_signals_for_company(conn, company_id)
    return {"signals": [signal.model_dump(mode="json") for signal in signals]}


def handle_get_contacts(arguments: dict[str, Any]) -> dict[str, Any]:
    company_id = int(arguments["company_id"])
    with get_connection() as conn:
        contacts = list_contacts_for_company(conn, company_id)
    return {"contacts": [contact.model_dump(mode="json") for contact in contacts]}


def handle_get_run_stats(arguments: dict[str, Any]) -> dict[str, Any]:
    run_id = arguments.get("run_id")
    with get_connection() as conn:
        runs = list_runs(conn)
    if run_id is None:
        return {"runs": [run.model_dump(mode="json") for run in runs]}
    run_id_int = int(run_id)
    selected = next((run for run in runs if run.run_id == run_id_int), None)
    if selected is None:
        raise ValueError(f"Run {run_id_int} not found")
    return {"run": selected.model_dump(mode="json")}


def handle_export_leads(arguments: dict[str, Any]) -> dict[str, Any]:
    run_id = arguments.get("run_id")
    limit = arguments.get("limit")
    min_score = arguments.get("min_score")

    with get_connection() as conn:
        companies = list_companies(conn, run_id=int(run_id) if run_id is not None else None)

    ranked = sorted(companies, key=lambda item: (item.score, item.id or 0), reverse=True)
    if min_score is not None:
        ranked = [company for company in ranked if company.score >= float(min_score)]
    if limit is not None:
        ranked = ranked[: int(limit)]

    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["id", "run_id", "name", "domain", "industry", "employee_count", "location", "score"])
    for company in ranked:
        writer.writerow(
            [
                company.id,
                company.run_id,
                company.name,
                company.domain,
                company.industry,
                company.employee_count,
                company.location,
                company.score,
            ]
        )

    return {
        "filename": "leads.csv",
        "content_type": "text/csv",
        "row_count": len(ranked),
        "csv": stream.getvalue(),
    }


def handle_trigger_run(arguments: dict[str, Any]) -> dict[str, Any]:
    user_id = arguments.get("user_id")
    status_value = arguments.get("status", RunStatus.queued.value)
    status = RunStatus(status_value)
    with get_connection() as conn:
        run_id = create_run(conn, user_id=int(user_id) if user_id is not None else None, status=status)
    return {"run_id": run_id, "status": status.value}


TOOL_HANDLERS: dict[str, ToolHandler] = {
    "search_companies": handle_search_companies,
    "leady.search_companies": handle_search_companies,
    "get_company": handle_get_company,
    "leady.get_company": handle_get_company,
    "get_top_leads": handle_get_top_leads,
    "leady.get_top_leads": handle_get_top_leads,
    "get_signals": handle_get_signals,
    "leady.get_signals": handle_get_signals,
    "get_contacts": handle_get_contacts,
    "leady.get_contacts": handle_get_contacts,
    "get_run_stats": handle_get_run_stats,
    "leady.get_run_stats": handle_get_run_stats,
    "export_leads": handle_export_leads,
    "leady.export_leads": handle_export_leads,
    "trigger_run": handle_trigger_run,
    "leady.trigger_run": handle_trigger_run,
}

WRITE_TOOLS = {"trigger_run", "leady.trigger_run"}


def execute_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        raise ValueError(f"Unknown tool '{tool_name}'")
    return handler(arguments)
