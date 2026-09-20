#!/usr/bin/env bash
# JailMap staging-source ingest wrapper.
# Runs each staging source (staging_only=true) independently with per-source logging.
set -uo pipefail

LOG_DIR="/root/jailmap/logs"
mkdir -p "$LOG_DIR"
DATE=$(date -u +%Y%m%d-%H%M%S)
LOG_FILE="$LOG_DIR/ingest-staging-${DATE}.log"

log() { echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') [ingest-staging] $*" | tee -a "$LOG_FILE"; }

log "Starting staging-source ingest"

SOURCES=$(docker compose exec -T postgres psql -U jailmap_owner -d jailmap -t -A -F'|' -c "
SELECT state||'|'||county
FROM records.jurisdictions
WHERE review_status='verified' AND staging_only=true
ORDER BY state, county;" 2>/dev/null)

OK=0
FAILED=0
TOTAL=0

while IFS='|' read -r STATE COUNTY; do
    [ -z "$STATE" ] && continue
    TOTAL=$((TOTAL + 1))
    log "--- $STATE / $COUNTY ---"
    RC=0
    docker compose exec -T api python -m backend.ingest --state "$STATE" --county "$COUNTY" >> "$LOG_FILE" 2>&1 </dev/null || RC=$?
    if [ $RC -eq 0 ]; then
        OK=$((OK + 1))
    else
        log "  FAILED $STATE/$COUNTY"
        FAILED=$((FAILED + 1))
    fi
done <<< "$SOURCES"

log "Staging-source ingest complete: $OK ok, $FAILED failed, $TOTAL total"

find "$LOG_DIR" -name 'ingest-staging-*.log' -mtime +7 -delete 2>/dev/null || true

[ $FAILED -eq 0 ] || exit 1
