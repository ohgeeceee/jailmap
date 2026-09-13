#!/bin/sh
# Usage: scripts/coverage.sh [--state MT]
set -eu
cd /root/jailmap
exec docker compose run --rm --no-deps -T --volume /root/jailmap/backend:/app/backend:ro api python -m backend.coverage "$@"
