#!/usr/bin/env bash
# Write vault notes with codex, N at a time. Separate model quota from Claude, which
# is exactly why this exists: a large Claude fan-out exhausts the Max session limit in
# minutes, and codex keeps the run alive.
#
#   codex-batch.sh <topics.json> <out-subdir> <template> [JOBS=2]
#
# topics.json: [{slug, mandate, tables?, objtype?}, ...]
# Restartable — a note already bigger than 3 KB is skipped.
set -uo pipefail
TOPICS="${1:?topics.json}"
SUB="${2:?out subdir, e.g. 02-documents}"
TPL="${3:?template file name, e.g. document-note.md}"
JOBS="${JOBS:-2}"

R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
V="$R/sap-b1/entry-vault"
ENVF=connections/hana-office-bridge.env
[ -f "$R/connections/hana-vps-direct.env" ] && ENVF=connections/hana-vps-direct.env
LOG="${LOG:-/tmp/codex-batch-$SUB.log}"
OUTD="${OUTD:-/tmp/codex-out-$SUB}"
mkdir -p "$V/$SUB" "$OUTD"
echo "=== start $(date) jobs=$JOBS topics=$TOPICS ===" >> "$LOG"

run_one() {
  slug="$1"; mandate="$2"
  dest="$V/$SUB/$slug.md"
  if [ -s "$dest" ] && [ "$(wc -c <"$dest")" -gt 3000 ]; then echo "skip $slug" >> "$LOG"; return; fi
  prompt="You are mining JIVO's live SAP HANA books to write ONE knowledge note. Work from $R.

READ FIRST, all of it:
  $V/bin/AGENT-BRIEF.md
  $V/_template/$TPL
  $R/harness/corrections/INDEX.md
  $V/00-index/Entry-Types-Census.md
  $R/acc/INVENTORY.md
Also read any note already in $V/01-foundations/ and $V/02-documents/ that your topic
depends on, and LINK to it with [[Wikilinks]] instead of restating it.
Pre-mined field profiles may already exist in $V/_data/ (profile-<TABLE>.md,
gl-<TransType>-<CO>.md, flow-<TABLE>-<CO>.md, sample-<TABLE>-OIL.md) — read those first,
they save you the query.

TOOLS (read-only; run from $R):
  python3 sap-b1/entry-vault/bin/profile.py <TABLE> [--co OIL,MART,BEV] [--days N] [--vocab-max N]
  python3 sap-b1/entry-vault/bin/gl.py <TransType> [--co OIL] [--days N] [--memo]
  python3 sap-b1/entry-vault/bin/flow.py <OTABLE> [--co OIL] [--days N]
  python3 sap-b1/entry-vault/bin/sample.py <OTABLE> --n 3 [--co OIL]
  ./hana-sql/hana-sql -env $ENVF \"SELECT ...\"
Schemas: JIVO_OIL_HANADB, JIVO_MART_HANADB, JIVO_BEVERAGES_HANADB.
Double-quote every SAP column: \"DocDate\". One SELECT per call.
On connection refused or timeout: run  bash sap-b1/entry-vault/bin/bridge.sh  then retry.
NEVER report 'no data' from a connection error.

HARD RULES:
- READ ONLY. Never write to SAP. Never run sapb1. SELECT only.
- Every number in the note must come from a query you actually ran, and the SQL goes in the note.
- Mark measured vs inferred explicitly. Never present an inference as a finding.
- The corrections in harness/corrections OUTRANK you. Contradicting one is a finding to report.
- This repo is PUBLIC. Field names, fill rates, GL codes and names, series numbers and vendor
  GROUP names are fine. Credentials, GSTINs (including VATRegNum values), bank account numbers,
  individual pay figures and bulk customer contact lists are NOT — never paste them.
- Say 'I don't know' under Open questions rather than guessing.

STYLE: Obsidian markdown, YAML front matter (type/sap_tables/objtype/companies/mined/confidence).
Tables over prose. Plain language first, SAP jargon second. Money in INR, Indian grouping, crores
for large numbers. The reader is an operator with the paper in their hand.

YOUR TOPIC: $slug

$mandate

Write the finished note to exactly this path: $dest
Cross-check all three books; a figure measured in Oil and asserted for Mart is the classic error.
Chase anything surprising rather than rounding it off. When done print only: WROTE <path> <bytes>"

  echo "--- $(date +%H:%M:%S) START $slug" >> "$LOG"
  ( cd "$R" && timeout 3600 codex exec --dangerously-bypass-approvals-and-sandbox "$prompt" ) \
      > "$OUTD/$slug.out" 2>&1
  rc=$?
  sz=$( [ -f "$dest" ] && wc -c <"$dest" || echo 0 )
  echo "--- $(date +%H:%M:%S) END   $slug rc=$rc bytes=$sz" >> "$LOG"
}

python3 - "$TOPICS" <<'PY' > "$OUTD/topics.tsv"
import json, sys
for t in json.load(open(sys.argv[1])):
    m = t['mandate']
    if t.get('tables'):
        m = f"SAP tables: {t['tables']}" + (f", ObjType/TransType {t['objtype']}" if t.get('objtype', -1) not in (None, -1) else "") + ". " + m
    print(t['slug'] + '\t' + m)
PY

n=0
while IFS=$'\t' read -r slug mandate; do
  [ -z "$slug" ] && continue
  run_one "$slug" "$mandate" &
  n=$((n+1))
  if [ $((n % JOBS)) -eq 0 ]; then wait; fi
done < "$OUTD/topics.tsv"
wait
echo "=== done $(date) ===" >> "$LOG"
