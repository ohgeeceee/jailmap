"""Shared helpers for the JailMap Green-tier bot scripts.

Read-only by construction: every query here is a SELECT, and every bot writes its
findings into its own agent-queue directory. Nothing in this package enables a
jurisdiction, publishes a record, starts a fetch, or sends anything outbound.
"""
import datetime
import os
import subprocess

ROOT = os.environ.get('JAILMAP_ROOT', '/root/jailmap')
PSQL = ['docker', 'exec', 'jailmap-postgres-1', 'psql', '-U', 'jailmap_owner', '-d', 'jailmap',
        '-tA', '-F', '|']


def query(sql, timeout=90):
    """Run a read-only query. Returns a list of '|'-joined rows, [] on any failure."""
    try:
        done = subprocess.run(PSQL + ['-c', sql], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return []
    if done.returncode != 0:
        return []
    return [line for line in done.stdout.splitlines() if line.strip()]


def today():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M')


def write_digest(bot, name, body):
    """Write a digest into agent-queue/<bot>/<date>-<name>.md and return its path."""
    directory = os.path.join(ROOT, 'agent-queue', bot)
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, '%s-%s.md' % (today(), name))
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(body.rstrip() + '\n')
    return path


def header(bot, title, green_note):
    return ('# %s - %s\n\nGenerated %sZ by `bots/`.\n\n%s\n'
            % (bot, title, stamp(), green_note))


def table(rows, columns):
    if not rows:
        return '_none_\n'
    out = ['| ' + ' | '.join(columns) + ' |', '|' + '---|' * len(columns)]
    for row in rows:
        out.append('| ' + ' | '.join(str(cell) for cell in row) + ' |')
    return '\n'.join(out) + '\n'
