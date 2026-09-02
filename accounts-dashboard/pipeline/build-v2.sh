#!/bin/bash
# build-v2.sh — the full v2 pipeline, end to end.
#
#   build_data.py   SAP HANA  ->  site/data.json        (unchanged, v1's engine)
#   split_data.py   data.json ->  site-v2/data/*.json   (manifest + 33 slices + parties)
#   derive.py       + derivations.<co>.json, KPI values into the manifest
#   verify.py       + the independent re-derivation of every KPI
#   history.py      + one point on site-v2/data/history.jsonl
#
# Every stage is a gate. A stage that fails leaves the previous site-v2/data
# untouched and exits non-zero, so the last good board keeps serving — the same
# contract v1 has, extended over the new stages.
#
#   ./build-v2.sh              full run, no deploy
#   ./build-v2.sh --deploy     ...then deploy and verify logged-out 200
#   ./build-v2.sh --skip-sap   re-run the v2 stages against the existing data.json
set -uo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$DIR")"
PROJECT="${V2_PROJECT:-jivo-accounts-v2}"
URL="https://${PROJECT}.vercel.app"
DEPLOY=0; SKIP_SAP=0
for a in "$@"; do
  case "$a" in
    --deploy)   DEPLOY=1 ;;
    --skip-sap) SKIP_SAP=1 ;;
    *) echo "unknown flag: $a" >&2; exit 64 ;;
  esac
done

[ "$(uname -s)" = "Linux" ] && export HANA_SQL_BIN="${HANA_SQL_BIN:-/usr/local/bin/hana-sql}"

say()  { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
stage() {
  local name="$1"; shift
  say "$name"
  if ! "$@"; then
    echo "STAGE FAILED: $name — previous site-v2/data left untouched" >&2
    exit 1
  fi
}

cd "$ROOT"
[ "$SKIP_SAP" -eq 1 ] || stage "1/5 build_data.py (SAP HANA -> data.json)" \
  python3 pipeline/build_data.py --no-guard
stage "2/5 split_data.py (manifest + slices + parties)" python3 pipeline/split_data.py
stage "3/5 derive.py (derivations + term closure)"      python3 pipeline/derive.py
stage "4/5 verify.py (independent re-derivation)"       python3 pipeline/verify.py
stage "5/5 history.py (trend point)"                    python3 pipeline/history.py

say "artefacts"
python3 - <<'PY'
import json, os, sys, glob
d = "site-v2/data"
man = json.load(open(os.path.join(d, "manifest.json")))
slices = sorted(glob.glob(os.path.join(d, "*.*.json")))
print("  generated_at   %s" % man.get("generated_at"))
print("  manifest       %.1f KB" % (os.path.getsize(os.path.join(d, "manifest.json")) / 1024))
print("  slices         %d" % len(slices))
print("  history points %s" % man.get("history_points"))
# ok is False = the two routes disagree. ok is None = no independent measurement
# exists for that KPI, which is a gap, not a contradiction. Counting them
# together would report 95 "disagreements" where there are 37.
bad = [(co, k, v.get("check"))
       for co, kd in (man.get("kpis") or {}).items()
       for k, v in kd.items()
       if isinstance(v.get("check"), dict) and v["check"].get("ok") is False]
nochk = sum(1 for kd in (man.get("kpis") or {}).values()
            for v in kd.values()
            if isinstance(v.get("check"), dict) and v["check"].get("ok") is None)
print("  KPIs           %d" % sum(len(k) for k in (man.get("kpis") or {}).values()))
if bad:
    print("  \033[31mCHECKS DISAGREEING: %d\033[0m" % len(bad))
    for co, k, c in bad[:12]:
        print("    %-5s %-34s primary vs alt delta %s" % (co, k, (c or {}).get("delta")))
    # A disagreement is reported, never hidden — but it does not block a publish,
    # because a number shown with a red dot beats a number not shown at all.
else:
    print("  checks         all agree")
print("  no independent measurement for %d KPI(s) — reported, not counted as disagreement" % nochk)
s = man.get("audit_summary") or {}
print("  roll-up facets %s" % ("all reconcile" if not s.get("rollup_disagreements") else "%d DISAGREE" % s["rollup_disagreements"]))
print("  cross-section  %s" % ("A/R and A/P agree by a second query" if s.get("cross_section_ok") else "DISAGREE"))
print("  corrections    %s" % ("all located in code" if not s.get("corrections_unverified") else "UNVERIFIED: %s" % s["corrections_unverified"]))
PY

if [ "$DEPLOY" -eq 1 ]; then
  say "deploy -> $PROJECT"
  ( cd "$ROOT/site-v2" && vercel deploy --prod --yes ) || { echo "DEPLOY FAILED" >&2; exit 1; }
  python3 "$DIR/vercel-public.py" "$PROJECT" >/dev/null 2>&1 || true
  CODE=$(curl -s -o /dev/null -w '%{http_code}' --max-time 25 "$URL" || echo 000)
  echo "  $URL -> HTTP $CODE"
  [ "$CODE" = "200" ] || { echo "NOT PUBLIC: $URL answered $CODE logged-out" >&2; exit 1; }
fi
