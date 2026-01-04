Generate monthly worklog from git commits

Usage

```sh
# generate for current month
python scripts/generate_worklog.py

# generate for January 2026
python scripts/generate_worklog.py 2026-01
```

The script writes to `worklogs/YYYY-MM.md`. It reads `WORKLOG-TEMPLATE.md` for the
header section when available and then appends daily commit summaries grouped by date.

If you want this to run automatically, add a GitHub Actions workflow that runs the
script daily and commits `worklogs/*.md` back to the repo.
