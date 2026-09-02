#!/usr/bin/env bash
# fetch-attachments.sh — pull a SAP B1 document's attachment files off the
# .52 Windows share, straight to a local folder. NO root, NO Service-Layer
# mount required: reads the attachment records from HANA, then copies the
# files over SMB from the hanadb box (which reaches the internal share).
#
# Usage:
#   fetch-attachments.sh --company OIL|MART|BEV --doc <DocEntry> [--doc N ...] \
#                        [--table ODRF|OPCH] [--out DIR]
#   (ODRF = drafts, OPCH = posted A/P invoices; default ODRF)
set -uo pipefail
REPO="/Users/damanpreetsingh/jivo-cli"
HS="/tmp/hs"; [ -x "$HS" ] || HS="$REPO/hana-sql/hana-sql"
SSH_HOST="jivo-sap-new"
COMPANY="OIL"; TABLE="ODRF"; OUT="./attachments-out"; DOCS=()
while [ $# -gt 0 ]; do case "$1" in
  --company) COMPANY="$2"; shift 2;;
  --table)   TABLE="$2";   shift 2;;
  --doc)     DOCS+=("$2"); shift 2;;
  --out)     OUT="$2";     shift 2;;
  *) echo "unknown arg: $1" >&2; exit 2;;
esac; done
[ ${#DOCS[@]} -gt 0 ] || { echo "need at least one --doc" >&2; exit 2; }
case "$COMPANY" in
  OIL)  SCHEMA=JIVO_OIL_HANADB;;
  MART) SCHEMA=JIVO_MART_HANADB;;
  BEV)  SCHEMA=JIVO_BEVERAGES_HANADB;;
  *) echo "company must be OIL|MART|BEV" >&2; exit 2;;
esac
set -a; source "$REPO/connections/hana-new.env"; source "$REPO/connections/new-servers.env"; set +a
mkdir -p "$OUT"

# stage the SMB credential on hanadb as a 600 authfile (password never on argv)
printf 'username=%s\npassword=%s\n' "$NEWWIN_SMB_USER" "$NEWWIN_SMB_PASS" \
  | ssh "$SSH_HOST" 'umask 077; cat > /tmp/.smbauth_fetch'
trap 'ssh "$SSH_HOST" "rm -f /tmp/.smbauth_fetch /tmp/att_fetch" 2>/dev/null' EXIT

got=0
for DOC in "${DOCS[@]}"; do
  echo "=== $COMPANY $TABLE DocEntry $DOC ==="
  ROWS=$("$HS" "SELECT L.\"FileName\" || '|~|' || L.\"FileExt\" || '|~|' || L.\"trgtPath\" FROM \"$SCHEMA\".\"ATC1\" L JOIN \"$SCHEMA\".\"$TABLE\" D ON L.\"AbsEntry\"=D.\"AtcEntry\" WHERE D.\"DocEntry\"=$DOC" 2>/dev/null | tail -n +2)
  if [ -z "$ROWS" ]; then echo "  (no attachments on this document)"; continue; fi
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    FN="${line%%|~|*}"; rest="${line#*|~|}"; EXT="${rest%%|~|*}"; TP="${rest#*|~|}"
    TP=$(printf '%s' "$TP" | sed 's/\\\\/\\/g')          # collapse escaped backslashes
    body="${TP#\\\\}"                                     # drop leading \\
    host="${body%%\\*}"; afterhost="${body#*\\}"
    share="${afterhost%%\\*}"; sub="${afterhost#*\\}"
    file="$FN.$EXT"; safe="${file//\//_}"
    printf '  -> %s\n' "$file"
    if ssh -n "$SSH_HOST" "smbclient '//$host/$share' -A /tmp/.smbauth_fetch -m SMB3 -c 'cd \"$sub\"; get \"$file\" /tmp/att_fetch'" >/dev/null 2>&1 \
       && scp -q "$SSH_HOST:/tmp/att_fetch" "$OUT/$safe"; then
      got=$((got+1))
    else
      echo "     !! failed to pull $file" >&2
    fi
  done <<< "$ROWS"
done
echo "--- fetched $got file(s) into $OUT ---"
ls -la "$OUT"
