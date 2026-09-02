#!/usr/bin/env bash
# run.sh - RM sheet vs live SAP stock, straight to Excel.
#
#   ./run.sh                        the newest sheet dropped in in/
#   ./run.sh in/01-09-2026.xlsx     a named sheet
#   ./run.sh in/sheet.xlsx --all-warehouses
set -euo pipefail
cd "$(dirname "$0")"

py=python3
command -v python3 >/dev/null 2>&1 || py=python

# a leading "-something" is a flag, not the sheet - so `./run.sh --itr` works
sheet=""
case "${1:-}" in
  ""|-*) ;;
  *) sheet="$1"; shift ;;
esac

if [ -z "$sheet" ]; then
  sheet=$(ls -1t in/*.xlsx in/*.csv in/*.txt in/*.tsv 2>/dev/null | head -1 || true)
fi
if [ -z "$sheet" ]; then
  echo "No sheet given and nothing in in/ - drop the RM sheet into $(pwd)/in/ first." >&2
  exit 1
fi

echo "Sheet: $sheet"
exec "$py" check.py "$sheet" "$@"
