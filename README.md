# timesheet-cli

A small, local-first command-line tool for logging hours by client and project,
computing weekly totals, and exporting CSV. Built and maintained by
[Asdale Dynamics, LLC](https://dylanasdale.github.io) — no accounts, no API
keys, no cloud. Your data stays in a plain JSON file on your machine.

## Who this is for

Freelancers, authors, small-business owners, and anyone who needs a dead-simple
way to track where their time goes. No setup beyond Python.

## Install

```bash
git clone <this-repo>
cd timesheet-cli
pip install -e .
```

Or just run it from the folder without installing:

```bash
python -m timesheet_cli --help
```

## Usage

Log some hours:

```bash
python -m timesheet_cli add "Acme Corp" "Website redesign" 3.5 --date 2026-10-26 --note "homepage layout"
```

List everything you have logged:

```bash
python -m timesheet_cli list
```

See weekly totals grouped by client and project:

```bash
python -m timesheet_cli weekly --week 2026-W43
```

Or report the week containing a specific date:

```bash
python -m timesheet_cli weekly --date 2026-10-28
```

Export all entries to CSV (opens in Excel, Google Sheets, etc.):

```bash
python -m timesheet_cli export hours.csv
```

## Where data lives

Entries are stored in `timesheet.json` in the current folder. Point the
`TIMESHEET_DATA` environment variable at another path if you prefer:

```bash
export TIMESHEET_DATA=~/timesheet.json
```

Everything is local-first. There is no server, no signup, and nothing leaves
your computer unless you choose to share the JSON or CSV file.

## Tests

```bash
python -m unittest discover -s tests -v
```

## License

MIT License. Copyright (c) 2026 Asdale Dynamics, LLC. See `LICENSE`.

Credit: Asdale Dynamics, LLC — beginner-friendly AI education, books and guides,
and practical open-source tools. https://dylanasdale.github.io
