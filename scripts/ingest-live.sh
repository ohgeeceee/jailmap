#!/usr/bin/env bash
# JailMap live-source ingest wrapper.
# Runs each live source independently with retry logic and per-source logging.
set -euo pipefail

LOG_DIR="/root/jailmap/logs"
mkdir -p "$LOG_DIR"
DATE=$(date -u +%Y%m%d-%H%M%S)
LOG_FILE="$LOG_DIR/ingest-live-${DATE}.log"

log() { echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') [ingest-live] $*" | tee -a "$LOG_FILE"; }

log "Starting live-source ingest"

SOURCES=$(docker compose exec -T postgres psql -U jailmap_owner -d jailmap -t -A -F'|' -c "
SELECT state||'|'||county
FROM records.jurisdictions
WHERE review_status='verified' AND enabled=true AND staging_only=false
ORDER BY state, county;" 2>/dev/null)

OK=0
FAILED=0
TOTAL=0

while IFS='|' read -r STATE COUNTY; do
    [ -z "$STATE" ] && continue
    TOTAL=$((TOTAL + 1))
    log "--- $STATE / $COUNTY ---"
    RETRIES=0
    MAX_RETRIES=2
    while [ $RETRIES -le $MAX_RETRIES ]; do
        RC=0
        docker compose exec -T api python -m backend.ingest --state "$STATE" --county "$COUNTY" >> "$LOG_FILE" 2>&1 < /dev/null || RC=$?
        if [ $RC -eq 0 ]; then
            OK=$((OK + 1))
            break
        else
            RETRIES=$((RETRIES + 1))
            if [ $RETRIES -le $MAX_RETRIES ]; then
                log "  retry $RETRIES/$MAX_RETRIES for $STATE/$COUNTY"
                sleep 10
            else
                log "  FAILED $STATE/$COUNTY after $MAX_RETRIES retries"
                FAILED=$((FAILED + 1))
            fi
        fi
    done
done <<< "$SOURCES"

log "Live-source ingest complete: $OK ok, $FAILED failed, $TOTAL total"

find "$LOG_DIR" -name 'ingest-live-*.log' -mtime +7 -delete 2>/dev/null || true

[ $FAILED -eq 0 ] || exit 1
