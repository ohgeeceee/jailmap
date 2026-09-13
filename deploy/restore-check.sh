#!/bin/bash
set -euo pipefail
umask 077
cd /root/jailmap
latest=$(find backups -maxdepth 1 -name 'jailmap-*.tar.gz.enc' -printf '%f\n' | sort | tail -1)
test -n "$latest"
work=$(mktemp -d /root/jailmap/backups/restore-check.XXXXXX)
cleanup() {
  docker compose exec -T postgres dropdb --if-exists -U jailmap_owner jailmap_restore_check >/dev/null
  rm -rf -- "$work"
}
trap cleanup EXIT
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass file:secrets/backup.key \
  -in "backups/$latest" | tar -xz -C "$work"
python3 - "$work/accounts.sqlite" <<'PY'
import sqlite3,sys
db=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True)
assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
assert db.execute("SELECT count(*) FROM sqlite_master WHERE name='accounts'").fetchone()[0] == 1
db.close()
print('Account backup integrity verified.')
PY
# Refuse to overwrite any existing database, including an earlier failed drill.
docker compose exec -T postgres createdb -U jailmap_owner jailmap_restore_check
docker compose exec -T postgres pg_restore -U jailmap_owner -d jailmap_restore_check --exit-on-error < "$work/records.dump"
docker compose exec -T postgres psql -U jailmap_owner -d jailmap_restore_check -Atc "SELECT count(*) FROM records.jurisdictions" >/dev/null
echo 'Encrypted backup decryption and isolated PostgreSQL restore verified.'
