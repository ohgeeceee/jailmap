#!/bin/bash
set -euo pipefail
umask 077
exec 9>/run/lock/jailmap-backup.lock
flock -n 9 || exit 0
cd /root/jailmap
stamp=$(date -u +%Y%m%dT%H%M%SZ)
work=$(mktemp -d /root/jailmap/backups/work.XXXXXX)
trap 'rm -rf -- "$work"' EXIT
docker compose exec -T postgres pg_dump -U jailmap_owner -d jailmap -Fc > "$work/records.dump"
python3 - "$work/accounts.sqlite" <<'PY'
import sqlite3, sys
source=sqlite3.connect('file:/root/jailmap/data/accounts/accounts.sqlite?mode=ro',uri=True)
target=sqlite3.connect(sys.argv[1])
source.backup(target)
assert target.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
source.close(); target.close()
PY
cp .env "$work/runtime.env"
cp compose.yaml "$work/compose.yaml"
if [[ -f compose.override.yaml ]]; then cp compose.override.yaml "$work/compose.override.yaml"; fi
# A running container can reference an image removed by earlier image cleanup.
# Inventory containers directly so that condition cannot prevent data backups.
docker compose ps --format json > "$work/containers.json"
tar -C "$work" -czf - . | openssl enc -aes-256-cbc -salt -pbkdf2 -iter 200000 \
  -pass file:secrets/backup.key -out "backups/jailmap-$stamp.tar.gz.enc"
sha256sum "backups/jailmap-$stamp.tar.gz.enc" > "backups/jailmap-$stamp.sha256"
# Only this application's dated backup archives are eligible for retention cleanup.
find /root/jailmap/backups -maxdepth 1 -type f -name 'jailmap-*.tar.gz.enc' -mtime +14 -delete
find /root/jailmap/backups -maxdepth 1 -type f -name 'jailmap-*.sha256' -mtime +14 -delete
echo "Encrypted JailMap backup completed: $stamp"
