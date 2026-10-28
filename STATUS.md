# STATUS

## What was built

A local-first Python CLI for time tracking: `timesheet-cli`. It logs hours by
client and project, computes weekly totals grouped by client/project, and
exports all entries to CSV. Data lives in a plain JSON file
(`timesheet.json` by default, or wherever `TIMESHEET_DATA` points). No
accounts, no API keys, no cloud, no personal data.

## Contents

- `timesheet_cli/store.py` — JSON storage (add/load/save entries, validation)
- `timesheet_cli/report.py` — ISO week math, weekly totals grouped by client/project
- `timesheet_cli/cli.py` — CLI: `add`, `list`, `weekly`, `export`
- `timesheet_cli/__main__.py` — enables `python -m timesheet_cli`
- `tests/test_timesheet.py` — 15 tests covering storage, CLI round-trip, totals, and date math
- `pyproject.toml` — project metadata and `timesheet` console script entry point
- `LICENSE` — MIT, `Copyright (c) 2026 Asdale Dynamics, LLC`
- `README.md` — usage guide, credits Asdale Dynamics, LLC
- `.gitignore` — excludes caches, data files, CSVs, builds

## How to run

```bash
# From the folder (no install required)
python3 -m timesheet_cli --help

# Log hours
python3 -m timesheet_cli add "Acme Corp" "Website" 3.5 --date 2026-10-26 --note "launch"

# List entries
python3 -m timesheet_cli list

# Weekly totals (ISO week)
python3 -m timesheet_cli weekly --week 2026-W44

# Weekly totals for the week containing a date
python3 -m timesheet_cli weekly --date 2026-10-28

# Export to CSV
python3 -m timesheet_cli export hours.csv

# Install the console script
pip install -e .
timesheet add "Acme Corp" "Website" 3.5
```

Data location: `timesheet.json` in the current folder, or override with
`TIMESHEET_DATA`.

## Verification results

- `python3 -m unittest discover -s tests -v` → **15 tests, OK** (all pass)
- Manual smoke test: `add`, `weekly`, `export` all run successfully; CSV output
  matches expected header and rows
- LICENSE line 3 is exactly `Copyright (c) 2026 Asdale Dynamics, LLC`
- README credits Asdale Dynamics, LLC
- No secrets, API keys, or personal data in any file
- No `.github/workflows` files
- Git initialized and committed (1 commit), working tree clean

## Known gaps

- No Python packaging/publishing step (intentionally not published per instructions)
- Entry editing/deletion not supported (append-only store)
- No config file beyond `TIMESHEET_DATA` environment variable
- No interactive/prompt mode; CLI-only
- Week grouping uses ISO calendar weeks (Monday–Sunday)
