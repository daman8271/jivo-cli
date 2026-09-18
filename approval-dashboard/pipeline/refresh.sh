#!/usr/bin/env bash
# One tick of the approval board. Cron runs this every minute:
#   * * * * * /root/jivo-cli/approval-dashboard/pipeline/refresh.sh
#
# The query is ~0.6s against all three books, so a minute is comfortable.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$ROOT/state/refresh.log"
mkdir -p "$ROOT/state"

# HANA lives behind the reverse tunnel the SAP box dials out to. The env file's
# own HANA_PORT still names 47301, which is the DEAD old box — these two must
# stay set here or every tick fails with "connection refused".
export HANA_HOST="${HANA_HOST:-127.0.0.1}"
export HANA_PORT="${HANA_PORT:-43015}"
export HANA_SQL_BIN="${HANA_SQL_BIN:-/opt/jivo-mcp/bin/hana-sql}"
export HANA_ENV_FILE="${HANA_ENV_FILE:-/opt/jivo-mcp/env/hana/hana.env}"

# A slow tick must never stack on the next one.
exec 9>"$ROOT/state/.refresh.lock"
flock -n 9 || exit 0

{
  python3 "$ROOT/pipeline/build.py" --once
  rc=$?
  # Alerts run even if a book failed: the books that did read still deserve their
  # alarm. build.py's own exit code carries the failure.
  python3 "$ROOT/pipeline/alerts.py" || true
  exit $rc
} >>"$LOG" 2>&1

# Keep the log from eating the disk — this runs 1,440 times a day.
if [ "$(wc -c <"$LOG" 2>/dev/null || echo 0)" -gt 2000000 ]; then
  tail -n 2000 "$LOG" >"$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi
