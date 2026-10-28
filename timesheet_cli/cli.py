"""Command-line interface for the timesheet tool."""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import date
from typing import Any, NoReturn

from . import __version__
from .report import parse_date, week_bounds, weekly_totals
from .store import add_entry, load_entries


def die(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def cmd_add(args: argparse.Namespace) -> None:
    entry_date = parse_date(args.date) if args.date else date.today()
    try:
        entry = add_entry(
            args.client,
            args.project,
            args.hours,
            entry_date,
            note=args.note or "",
        )
    except ValueError as exc:
        die(str(exc))
    print(
        f"logged {entry['hours']}h for {entry['client']} / {entry['project']} "
        f"on {entry['date']}"
    )


def cmd_list(args: argparse.Namespace) -> None:
    entries = load_entries()
    if not entries:
        print("no entries yet")
        return
    print(f"{'DATE':<12} {'HOURS':<7} {'CLIENT':<20} {'PROJECT':<20} NOTE")
    print("-" * 70)
    for entry in entries:
        print(
            f"{entry.get('date',''):<12} "
            f"{entry.get('hours',0):<7} "
            f"{str(entry.get('client','')):<20} "
            f"{str(entry.get('project','')):<20} "
            f"{entry.get('note','')}"
        )


def cmd_weekly(args: argparse.Namespace) -> None:
    if args.week:
        try:
            year_str, week_str = args.week.split("-W")
            year, week = int(year_str), int(week_str)
        except (ValueError, AttributeError):
            die(f"invalid week format '{args.week}', expected YYYY-WNN")
    elif args.date:
        entry_date = parse_date(args.date)
        year, week, _ = entry_date.isocalendar()
    else:
        today = date.today()
        year, week, _ = today.isocalendar()

    report = weekly_totals(year=year, week=week)
    print(f"week {report['week_label']} ({report['week_start']} to {report['week_end']})")
    if not report["groups"]:
        print("no entries")
        return
    for client in sorted(report["groups"]):
        for project in sorted(report["groups"][client]):
            hours = report["groups"][client][project]
            print(f"  {client:<20} {project:<20} {hours}h")
    print(f"  {'TOTAL':<40} {report['total_hours']}h")


def cmd_export(args: argparse.Namespace) -> None:
    entries = load_entries()
    with open(args.output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "date", "client", "project", "hours", "note"])
        for entry in entries:
            writer.writerow(
                [
                    entry.get("id", ""),
                    entry.get("date", ""),
                    entry.get("client", ""),
                    entry.get("project", ""),
                    entry.get("hours", 0),
                    entry.get("note", ""),
                ]
            )
    print(f"exported {len(entries)} entries to {args.output}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="timesheet",
        description="Log hours by client and project, compute weekly totals, export CSV.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="log hours for a client/project")
    p_add.add_argument("client", help="client name")
    p_add.add_argument("project", help="project name")
    p_add.add_argument("hours", type=float, help="hours worked")
    p_add.add_argument("--date", help="YYYY-MM-DD (defaults to today)")
    p_add.add_argument("--note", default="", help="optional note")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="list all logged entries")
    p_list.set_defaults(func=cmd_list)

    p_weekly = sub.add_parser("weekly", help="show weekly totals by client/project")
    p_weekly.add_argument("--week", help="YYYY-WNN ISO week (defaults to current week)")
    p_weekly.add_argument("--date", help="YYYY-MM-DD; report its ISO week")
    p_weekly.set_defaults(func=cmd_weekly)

    p_export = sub.add_parser("export", help="export all entries to CSV")
    p_export.add_argument("output", help="output CSV path")
    p_export.set_defaults(func=cmd_export)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
