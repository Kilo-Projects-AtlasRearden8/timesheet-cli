"""Unit tests for the timesheet store, report, and CLI."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import date

from timesheet_cli.report import parse_date, week_bounds, week_key, weekly_totals
from timesheet_cli.store import add_entry, load_entries


class TempFileTests(unittest.TestCase):
    """Tests that run against a temporary JSON storage file."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmpdir.name, "timesheet.json")
        os.environ["TIMESHEET_DATA"] = self.path

    def tearDown(self) -> None:
        self.tmpdir.cleanup()
        os.environ.pop("TIMESHEET_DATA", None)

    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "timesheet_cli", *args],
            capture_output=True,
            text=True,
        )


class StoreTests(TempFileTests):
    def test_add_and_load_entry(self):
        entry = add_entry("Acme", "Website", 3.5, date(2026, 10, 26), note="launch")
        entries = load_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["client"], "Acme")
        self.assertEqual(entries[0]["project"], "Website")
        self.assertEqual(entries[0]["hours"], 3.5)
        self.assertEqual(entries[0]["date"], "2026-10-26")
        self.assertEqual(entries[0]["note"], "launch")
        self.assertTrue(entries[0]["id"])

    def test_persists_across_reloads(self):
        add_entry("Acme", "Website", 2.0, date(2026, 10, 26))
        again = load_entries()
        self.assertEqual(len(again), 1)

    def test_negative_hours_rejected(self):
        with self.assertRaises(ValueError):
            add_entry("Acme", "Website", -1.0, date(2026, 10, 26))

    def test_empty_client_rejected(self):
        with self.assertRaises(ValueError):
            add_entry("", "Website", 1.0, date(2026, 10, 26))

    def test_bad_json_file_yields_empty(self):
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write("{not valid json")
        self.assertEqual(load_entries(), [])

    def test_cli_add_round_trip(self):
        result = self.run_cli("add", "Acme", "Website", "3.5", "--date", "2026-10-26")
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_cli("list")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Acme", result.stdout)
        self.assertIn("Website", result.stdout)
        self.assertIn("3.5", result.stdout)


class DateMathTests(TempFileTests):
    def test_week_key_format(self):
        # 2026-10-26 is a Monday in ISO week 2026-W44
        self.assertEqual(week_key(date(2026, 10, 26)), "2026-W44")
        self.assertEqual(week_key(date(2026, 1, 1)), "2026-W01")

    def test_week_bounds_monday_to_sunday(self):
        start, end = week_bounds(date(2026, 10, 26))
        self.assertEqual(start, date(2026, 10, 26))
        self.assertEqual(end, date(2026, 11, 1))

        # A Sunday still bounds the same week
        start, end = week_bounds(date(2026, 11, 1))
        self.assertEqual(start, date(2026, 10, 26))
        self.assertEqual(end, date(2026, 11, 1))

    def test_week_spans_year_boundary(self):
        start, end = week_bounds(date(2026, 1, 1))
        self.assertEqual(start, date(2025, 12, 29))
        self.assertEqual(end, date(2026, 1, 4))

    def test_parse_date_valid_and_invalid(self):
        self.assertEqual(parse_date("2026-10-26"), date(2026, 10, 26))
        with self.assertRaises(ValueError):
            parse_date("not-a-date")
        with self.assertRaises(ValueError):
            parse_date("2026-13-01")


class TotalsTests(TempFileTests):
    def setUp(self) -> None:
        super().setUp()
        # Monday Oct 26 2026 (week 2026-W44)
        add_entry("Acme", "Website", 3.5, date(2026, 10, 26))
        add_entry("Acme", "Website", 2.0, date(2026, 10, 27), note="fixes")
        add_entry("Acme", "Docs", 1.0, date(2026, 10, 28))
        add_entry("Globex", "API", 4.0, date(2026, 10, 29))
        # Next week, should not appear in W44 totals
        add_entry("Acme", "Website", 8.0, date(2026, 11, 2))

    def test_weekly_totals_group_by_client_and_project(self):
        report = weekly_totals(year=2026, week=44)
        self.assertEqual(report["week_label"], "2026-W44")
        self.assertEqual(report["week_start"], "2026-10-26")
        self.assertEqual(report["week_end"], "2026-11-01")
        self.assertEqual(report["groups"]["Acme"]["Website"], 5.5)
        self.assertEqual(report["groups"]["Acme"]["Docs"], 1.0)
        self.assertEqual(report["groups"]["Globex"]["API"], 4.0)
        self.assertEqual(report["total_hours"], 10.5)

    def test_excludes_other_weeks(self):
        report = weekly_totals(year=2026, week=45)
        self.assertEqual(report["groups"]["Acme"]["Website"], 8.0)
        self.assertEqual(report["total_hours"], 8.0)

    def test_defaults_to_current_week(self):
        report = weekly_totals()
        today = date.today()
        year, week, _ = today.isocalendar()
        self.assertEqual(report["year"], year)
        self.assertEqual(report["week"], week)

    def test_cli_weekly_output(self):
        self.run_cli("add", "Acme", "Website", "3.5", "--date", "2026-10-26")
        result = self.run_cli("weekly", "--week", "2026-W44")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2026-W44", result.stdout)
        self.assertIn("Acme", result.stdout)
        self.assertIn("Website", result.stdout)
        self.assertIn("9.0h", result.stdout)
        self.assertIn("14.0h", result.stdout)
        self.assertIn("TOTAL", result.stdout)

    def test_export_writes_csv(self):
        result = self.run_cli("export", os.path.join(self.tmpdir.name, "out.csv"))
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(os.path.join(self.tmpdir.name, "out.csv"), encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        self.assertEqual(rows[0], ["id", "date", "client", "project", "hours", "note"])
        # 5 entries seeded in setUp, plus the header row
        self.assertEqual(len(rows), 6)


if __name__ == "__main__":
    unittest.main()
