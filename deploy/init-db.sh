#!/bin/sh
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=app_password="$PG_APP_PASSWORD" <<'SQL'
CREATE ROLE jailmap_app LOGIN PASSWORD :'app_password';
SQL
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /bootstrap/records.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /bootstrap/map.sql
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
GRANT CONNECT ON DATABASE jailmap TO jailmap_app;
GRANT USAGE ON SCHEMA records,public TO jailmap_app;
GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA records TO jailmap_app;
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA records TO jailmap_app;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO jailmap_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA records GRANT SELECT,INSERT,UPDATE,DELETE ON TABLES TO jailmap_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA records GRANT USAGE,SELECT ON SEQUENCES TO jailmap_app;
SQL
