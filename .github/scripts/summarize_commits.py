#!/usr/bin/env python3
import os
import subprocess
import datetime

def run_git(args):
    return subprocess.check_output(args, text=True)

def main():
    input_date = os.environ.get('INPUT_DATE') or os.environ.get('TARGET_DATE')
    if not input_date:
        today = datetime.datetime.utcnow().date()
        target = today - datetime.timedelta(days=1)
        input_date = target.isoformat()
    target_date = input_date
    since = f"{target_date}T00:00:00"
    until = f"{target_date}T23:59:59"
    author = os.environ.get('WORKLOG_AUTHOR_EMAIL') or os.environ.get('WORKLOG_AUTHOR')
    args = [
        'git',
        'log',
        f"--since={since}",
        f"--until={until}",
        "--pretty=format:%H|%an|%ae|%ad|%s",
        "--date=iso",
    ]
    try:
        output = run_git(args)
    except subprocess.CalledProcessError:
        print('No commits or git error')
        return
    if not output.strip():
        print('No commits for', target_date)
        return
    lines = [l for l in output.splitlines()]
    if author:
        lines = [l for l in lines if f'|{author}|' in l or l.split('|')[2] == author]
    if not lines:
        print('No commits for author on', target_date)
        return
    bullets = []
    for l in lines:
        sha, name, email, date, subject = l.split('|', 4)
        short = sha[:7]
        bullets.append(f"- {short} — {subject} ({name})")
    header = f"### {target_date} — Commits summary\n\n"
    body = header + "\n".join(bullets) + "\n\n"
    monthfile = os.path.join('worklogs', target_date[:7] + '.md')
    if not os.path.exists('worklogs'):
        os.makedirs('worklogs', exist_ok=True)
    if not os.path.exists(monthfile):
        if os.path.exists('WORKLOG-TEMPLATE.md'):
            with open('WORKLOG-TEMPLATE.md', 'r', encoding='utf-8') as t:
                tmpl = t.read()
            with open(monthfile, 'w', encoding='utf-8') as f:
                f.write(tmpl + '\n')
        else:
            with open(monthfile, 'w', encoding='utf-8') as f:
                f.write(f"# Worklog - {target_date[:7]}\n\n")
    with open(monthfile, 'a', encoding='utf-8') as f:
        f.write(body)
    print('Appended summary to', monthfile)

if __name__ == '__main__':
    main()
