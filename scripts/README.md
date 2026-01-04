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

Assets embedding
----------------

Place screenshots or other demo files under `assets/YYYY-MM/` (for example `assets/2026-01/`).
The generator will automatically embed images (PNG/JPG/GIF/WEBP) and link other files in
the generated monthly file. If an asset filename includes a date prefix like
`2026-01-05-screenshot.png`, the asset will also be attached to that specific day's
section when using `--day YYYY-MM-DD`.

