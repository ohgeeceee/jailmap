#!/bin/sh
# Run a scripts/national/*.py tool inside the jailmap-api container, which holds
# DATABASE_URL and psycopg.
#
# /root/jailmap is mode 700, so the container's uid 1000 cannot traverse the repo
# root. Mount the individual subtrees instead — the docker daemon resolves the
# source paths as root, so the mounts succeed even though the parent is 0700.
#
#   /tools        -> scripts/national   (this directory)
#   /src/states   -> states             (adapter scaffolding census)
#   /src/backend  -> backend            (adapter registry)
#
# Usage: scripts/national/run.sh audit_coverage.py --markdown
set -eu
cd /root/jailmap
if [ "$#" -eq 0 ]; then
  echo "usage: $0 <script.py> [args...]" >&2
  exit 64
fi
script=$1
shift
exec docker compose run --rm --no-deps -T \
  --volume /root/jailmap/scripts/national:/tools:ro \
  --volume /root/jailmap/states:/src/states:ro \
  --volume /root/jailmap/backend:/src/backend:ro \
  --volume /root/jailmap/data:/src/data:rw \
  --env JAILMAP_REPO=/src \
  --env PYTHONPATH=/src \
  api python "/tools/${script}" "$@"
