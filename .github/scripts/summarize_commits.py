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
    details = []
    for l in lines:
        sha, name, email, date, subject = l.split('|', 4)
        short = sha[:7]
        bullets.append(f"- {short} — {subject} ({name})")
        # get files changed
        try:
            files_out = run_git(['git', 'show', '--name-only', '--pretty=format:', sha])
            files = [f for f in files_out.splitlines() if f.strip()]
        except subprocess.CalledProcessError:
            files = []
        # get full commit body
        try:
            body_out = run_git(['git', 'show', '--pretty=format:%B', '-s', sha])
        except subprocess.CalledProcessError:
            body_out = ''
        details.append({
            'sha': sha,
            'short': short,
            'name': name,
            'email': email,
            'date': date,
            'subject': subject,
            'files': files,
            'body': body_out.strip(),
        })

    header = f"### {target_date} — Commits summary\n\n"
    summary_block = header + "\n".join(bullets) + "\n\n"
    # Build detailed block
    details_block = "#### Details\n\n"
    for d in details:
        details_block += f"- {d['short']} — {d['subject']} ({d['name']})\n"
        details_block += f"  - Date: {d['date']}\n"
        if d['files']:
            details_block += f"  - Files:\n"
            for f in d['files']:
                details_block += f"    - {f}\n"
        if d['body']:
            # indent body lines
            body_lines = d['body'].splitlines()
            details_block += f"  - Message:\n"
            for bl in body_lines:
                details_block += f"    {bl}\n"
        details_block += "\n"

    body = summary_block + details_block
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

    # Read existing content and replace existing block for the target_date if present
    with open(monthfile, 'r', encoding='utf-8') as f:
        content = f.read()

    start_marker = f"### {target_date} — Commits summary"
    if start_marker in content:
        # remove existing block from start_marker to next '### ' or EOF
        parts = content.split(start_marker, 1)
        prefix = parts[0]
        rest = parts[1]
        # find next '### ' occurrence
        next_idx = rest.find('\n### ')
        if next_idx != -1:
            suffix = rest[next_idx+1:]
        else:
            suffix = ''
        new_content = prefix + start_marker + '\n\n' + body + suffix
    else:
        new_content = content + '\n' + body

    with open(monthfile, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Updated worklog with detailed summary:', monthfile)

if __name__ == '__main__':
    main()
