"""Google Sheets export integration, gated by ENABLE_GOOGLE_SHEETS=true."""

from __future__ import annotations

import os

import requests

DEFAULT_WORKSHEET_NAME = "Sheet1"


def google_sheets_enabled() -> bool:
    return os.getenv("ENABLE_GOOGLE_SHEETS", "false").strip().lower() == "true"


def append_rows_to_google_sheets(headers: list[str], rows: list[list[object]]) -> dict[str, object]:
    """Append rows to Google Sheets Values API when explicitly enabled."""
    if not google_sheets_enabled():
        return {"enabled": False, "detail": "Google Sheets integration disabled"}

    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
    access_token = os.getenv("GOOGLE_SHEETS_ACCESS_TOKEN", "").strip()
    worksheet_name = os.getenv("GOOGLE_SHEETS_WORKSHEET", DEFAULT_WORKSHEET_NAME).strip() or DEFAULT_WORKSHEET_NAME

    if not spreadsheet_id or not access_token:
        return {
            "enabled": True,
            "synced": False,
            "detail": "Missing GOOGLE_SHEETS_SPREADSHEET_ID or GOOGLE_SHEETS_ACCESS_TOKEN",
        }

    endpoint = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/"
        f"values/{worksheet_name}!A1:append?valueInputOption=RAW"
    )
    payload = {"values": [headers, *rows]}
    response = requests.post(
        endpoint,
        json=payload,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=15,
    )
    response.raise_for_status()
    return {
        "enabled": True,
        "synced": True,
        "updated_range": response.json().get("updates", {}).get("updatedRange"),
        "rows_sent": len(rows),
    }
