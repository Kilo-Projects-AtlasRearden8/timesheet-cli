"""JSON storage for timesheet entries.

Local-first: entries live in a plain JSON file (default ``timesheet.json`` in
the current directory, or wherever ``TIMESHEET_DATA`` points).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import date
from typing import Any

def _default_path() -> str:
    return os.environ.get("TIMESHEET_DATA", "timesheet.json")


def load_entries(path: str | None = None) -> list[dict[str, Any]]:
    """Load all entries from the storage file."""
    if path is None:
        path = _default_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [entry for entry in data if isinstance(entry, dict)]


def save_entries(entries: list[dict[str, Any]], path: str | None = None) -> None:
    """Persist all entries to the storage file."""
    if path is None:
        path = _default_path()
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(entries, handle, indent=2)
        handle.write("\n")


def add_entry(
    client: str,
    project: str,
    hours: float,
    entry_date: date,
    note: str = "",
    path: str | None = None,
) -> dict[str, Any]:
    """Append a validated entry and return it."""
    hours = float(hours)
    if hours < 0:
        raise ValueError("hours must be non-negative")
    client = client.strip()
    project = project.strip()
    if not client or not project:
        raise ValueError("client and project are required")
    entry: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "client": client,
        "project": project,
        "hours": round(hours, 4),
        "date": entry_date.isoformat(),
        "note": str(note),
    }
    entries = load_entries(path)
    entries.append(entry)
    save_entries(entries, path)
    return entry
