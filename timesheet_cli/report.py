"""Reports and date math for timesheet entries."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from .store import load_entries


def parse_date(value: str) -> date:
    """Parse an ISO-format date string, raising ValueError on bad input."""
    return date.fromisoformat(value.strip())


def week_key(entry_date: date) -> str:
    """ISO week label like ``2026-W43`` for the week containing ``entry_date``."""
    iso_year, iso_week, _iso_weekday = entry_date.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def week_bounds(entry_date: date) -> tuple[date, date]:
    """Return (Monday, Sunday) bounding the ISO week of ``entry_date``."""
    iso_year, iso_week, iso_weekday = entry_date.isocalendar()
    monday = entry_date - timedelta(days=iso_weekday - 1)
    sunday = monday + timedelta(days=6)
    return monday, sunday


def _entries_in_week(
    entries: list[dict[str, Any]], year: int, week: int
) -> list[dict[str, Any]]:
    matched = []
    for entry in entries:
        try:
            entry_date = date.fromisoformat(entry["date"])
        except (KeyError, ValueError, TypeError):
            continue
        iso_year, iso_week, _ = entry_date.isocalendar()
        if iso_year == year and iso_week == week:
            matched.append(entry)
    return matched


def weekly_totals(
    entries: list[dict[str, Any]] | None = None,
    year: int | None = None,
    week: int | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    """Sum hours grouped by client and project for one ISO week.

    Returns a dict with ``year``, ``week``, ``week_label``, ``week_start``,
    ``week_end``, ``groups`` (client -> project -> hours), and ``total_hours``.
    """
    if entries is None:
        entries = load_entries(path)

    today = date.today()
    if year is None:
        year = today.isocalendar()[0]
    if week is None:
        week = today.isocalendar()[1]

    week_label = f"{year}-W{week:02d}"
    # Anchor the week label to an actual date: Monday of that ISO week.
    jan4 = date(year, 1, 4)
    week1_monday = jan4 - timedelta(days=(jan4.isoweekday() - 1))
    week_start = week1_monday + timedelta(weeks=week - 1)
    week_end = week_start + timedelta(days=6)

    groups: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for entry in _entries_in_week(entries, year, week):
        client = entry.get("client", "Unknown")
        project = entry.get("project", "Unknown")
        try:
            hours = float(entry.get("hours", 0))
        except (TypeError, ValueError):
            hours = 0.0
        groups[client][project] += hours

    rounded_groups = {
        client: {project: round(hours, 2) for project, hours in projects.items()}
        for client, projects in groups.items()
    }
    total_hours = round(
        sum(hours for projects in groups.values() for hours in projects.values()), 2
    )

    return {
        "year": year,
        "week": week,
        "week_label": week_label,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "groups": rounded_groups,
        "total_hours": total_hours,
    }
