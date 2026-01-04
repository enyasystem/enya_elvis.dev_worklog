#!/usr/bin/env python3
"""
Generate a monthly worklog markdown from git commit messages.

Usage:
  python scripts/generate_worklog.py 2026-01
  python scripts/generate_worklog.py --month 2026-01
  python scripts/generate_worklog.py         # defaults to current month

The script writes to `worklogs/YYYY-MM.md` using the `WORKLOG-TEMPLATE.md`
header when present and appends daily commit summaries grouped by date.
"""
from __future__ import annotations
import subprocess
import sys
import datetime
import os
from collections import defaultdict


def run_git(args):
    proc = subprocess.run(["git"] + args, capture_output=True, text=True)
    proc.check_returncode()
    return proc.stdout


def get_commits(since: datetime.datetime, until: datetime.datetime):
    fmt = "%H%x01%ad%x01%an%x01%s"
    args = [
        "log",
        f"--since={since.isoformat()}",
        f"--until={until.isoformat()}",
        f"--pretty=format:{fmt}",
        "--date=iso-strict",
    ]
    out = run_git(args)
    commits = []
    for line in out.splitlines():
        parts = line.split("\x01")
        if len(parts) < 4:
            continue
        sha, datestr, author, subject = parts[:4]
        try:
            dt = datetime.datetime.fromisoformat(datestr)
        except Exception:
            # fallback to naive parsing
            dt = datetime.datetime.strptime(datestr, "%Y-%m-%d %H:%M:%S %z")
        commits.append({"sha": sha, "date": dt, "author": author, "message": subject})
    return commits


def get_files_for_commit(sha: str):
    out = run_git(["show", "--name-only", "--pretty=format:", "--no-patch", sha])
    return [l for l in out.splitlines() if l.strip()]


def month_range(year: int, month: int):
    start = datetime.datetime(year, month, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    if month == 12:
        end = datetime.datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    else:
        end = datetime.datetime(year, month + 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    return start, end


def load_template():
    tpl_path = os.path.join(os.getcwd(), "WORKLOG-TEMPLATE.md")
    if os.path.exists(tpl_path):
        with open(tpl_path, "r", encoding="utf-8") as f:
            return f.read()
    # minimal fallback header
    return "# {Month YYYY} — Monthly Worklog\n\n" 


def format_month_header(template: str, year: int, month: int):
    name = datetime.date(year, month, 1).strftime("%B %Y")
    return template.replace("{Month YYYY}", name)


def build_markdown(year: int, month: int, commits):
    tpl = load_template()
    header = format_month_header(tpl, year, month)
    lines = [header, "\n"]

    # group commits by local date
    groups = defaultdict(list)
    for c in commits:
        local_date = c["date"].astimezone().date()
        groups[local_date].append(c)

    for day in sorted(groups.keys()):
        day_str = day.isoformat()
        lines.append(f"### {day_str} — Commits summary\n\n")
        for c in groups[day]:
            short = c["sha"][:7]
            lines.append(f"- {short} — {c['message']} ({c['author']})\n")
        lines.append("\n#### Details\n\n")
        for c in groups[day]:
            short = c["sha"][:7]
            lines.append(f"- {short} — {c['message']} ({c['author']})\n")
            lines.append(f"  - Date: {c['date'].astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}\n")
            files = get_files_for_commit(c["sha"])[:20]
            if files:
                lines.append("  - Files:\n")
                for f in files:
                    lines.append(f"    - {f}\n")
            else:
                lines.append("  - Files: (none)\n")
            lines.append("  - Message:\n")
            lines.append(f"    - {c['message']}\n\n")

    return "".join(lines)


def write_worklog(year: int, month: int, content: str):
    out_dir = os.path.join(os.getcwd(), "worklogs")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{year}-{month:02d}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {path}")


def parse_args(argv):
    if len(argv) >= 2 and not argv[1].startswith("--"):
        token = argv[1]
    else:
        token = None
    if token:
        parts = token.split("-")
        if len(parts) >= 2:
            year = int(parts[0]); month = int(parts[1])
            return year, month
    # default: current month
    now = datetime.datetime.now()
    return now.year, now.month


def main(argv):
    year, month = parse_args(argv)
    start, end = month_range(year, month)
    commits = get_commits(start, end)
    if not commits:
        print("No commits found for the month.")
    content = build_markdown(year, month, commits)
    write_worklog(year, month, content)


if __name__ == "__main__":
    main(sys.argv)
