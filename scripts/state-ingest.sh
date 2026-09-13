#!/bin/sh
# Usage: scripts/state-ingest.sh MT --dry-run (omit --dry-run to commit)
set -eu
cd /root/jailmap
state=${1:?Supply a two-letter state code}
shift
exec docker compose run --rm --no-deps -T --volume /root/jailmap/backend:/app/backend:ro api python -m backend.ingest --state "$state" "$@"
