#!/bin/bash
# Rolling refresh: re-read SAP, re-plan what is LEFT of the month, redeploy the site.
#
#   engine/refresh.sh              today becomes day 1, plan the rest of the month
#   engine/refresh.sh 2026-09-01   pin the as-of date
#   DEPLOY=0 engine/refresh.sh     rebuild locally, do not publish
#
# Every stage is gated. If a stage fails the run STOPS and the live site keeps the
# last good plan — a stale plan a human trusts is worse than yesterday's plan they know.
set -euo pipefail
cd "$(dirname "$0")/.."                                  # jolly/
JOLLY="$PWD"; REPO="$(dirname "$PWD")"
ASOF="${1:-$(date +%F)}"
LOG="$JOLLY/out/refresh-$ASOF.log"
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }

say "=== rolling refresh, as-of $ASOF ==="

# 0 — SAP reachable? The Mac goes through a tunnel that dies with sleep; the VPS reaches
#     HANA directly. Try every env this box has, and only tunnel if none answers.
HANA_ENV=""
for e in hana-office-bridge hana-vps-direct hana-vps hana; do
  [ -f "$REPO/connections/$e.env" ] || continue
  if "$REPO/hana-sql/hana-sql" -env "$REPO/connections/$e.env" "SELECT 1 FROM DUMMY" >/dev/null 2>&1; then
    HANA_ENV="$e"; break
  fi
done
if [ -z "$HANA_ENV" ]; then
  say "no HANA env answered — trying the tunnel"
  nohup ssh -N -L 13015:127.0.0.1:43015 -L 15000:127.0.0.1:45000 vps >/dev/null 2>&1 &
  sleep 8
  for e in hana-office-bridge hana-tunnel; do
    [ -f "$REPO/connections/$e.env" ] || continue
    "$REPO/hana-sql/hana-sql" -env "$REPO/connections/$e.env" "SELECT 1 FROM DUMMY" >/dev/null 2>&1 && { HANA_ENV="$e"; break; }
  done
fi
[ -n "$HANA_ENV" ] || { say "ABORT: HANA unreachable from $(hostname)"; exit 1; }
export HANA_ENV
say "HANA ok via $HANA_ENV"

# 1 — keep the last good inputs, so a bad freeze can be rolled back by hand
cp sim/sep-inputs.json "sim/sep-inputs.prev.json" 2>/dev/null || true

# 2 — freeze from live SAP + EXIM. Rolling: opening = stock NOW, horizon = ASOF..month end,
#     and the month's plan is netted by what the floor has already produced (OIGN).
SIM_ASOF="$ASOF" python3 engine/freeze_sep.py 2>&1 | tee -a "$LOG"

# 3 — simulate the baseline and every scenario on the SAME inputs (never mix vintages:
#     a scenario compared against a differently-frozen baseline is a fabricated delta)
sim(){ (
    export SIM_INPUTS=sim/sep-inputs.json SIM_TAG="$1" SIM_HOURS="$2" SIM_SUNDAYS_OFF="$3"
    [ -n "${4:-}" ] && export SIM_HOURS_SCHEDULE="$4"
    python3 engine/august_sim.py >/dev/null
  ) || { say "ABORT: sim $1 failed"; exit 1; }
  say "  sim $1"; }
sim -sep 12 1
sim -sep-12x31 12 0
sim -sep-22x31 22 0
sim -sep-24x31 24 0
sim -sep-taper 12 0 "1-13:22,14-30:12"
sim -sep-taper18 12 0 "1-13:22,14-30:18"

# 4 — conservation law: oil consumed must reconcile to litres produced. This is the
#     check that once caught a 2.29x double-count whose output looked perfect.
python3 - "$ASOF" <<'PY' 2>&1 | tee -a "$LOG"
import json, sys
s = json.load(open('sim/summary-sep.json')); t = s['totals']
made, oil = t['made_l'], t.get('oil_used_l', 0)
gap = abs(oil - made) / max(made, 1) * 100
ship = t['shipped_l']
pins = sum(1 for d in s['days'] if d['storage_pct'] >= 99.95)
dead = sum(1 for d in s['days'] if d['working'] and d['shipped_l'] == 0)
neg = t.get('negative_stocks') or {}
print(f"  made {made:,} L | shipped {ship:,} L | value Rs {t['value']/1e7:.2f} Cr")
print(f"  conservation {gap:.3f}% | storage-pinned days {pins} | non-shipping working days {dead}")
fail = []
if gap > 5: fail.append(f"conservation {gap:.2f}% > 5%")
if neg: fail.append(f"negative stocks: {list(neg)[:3]}")
if made <= 0: fail.append("nothing produced")
if dead > 5: fail.append(f"{dead} working days ship nothing")
if pins > 10: fail.append(f"godown pinned {pins} days — check the freeze")
if fail: print("GATE FAILED: " + "; ".join(fail)); sys.exit(1)
print("  gates PASS")
PY

# 5 — the operator-facing artifacts, rebuilt from THIS run (the site generator refuses
#     to write if these are older than the sim, so they must be regenerated here)
python3 engine/sep_gap.py --inputs sim/sep-inputs.json --days-dir sim/days-sep \
        --csv out/order-by-sep.csv --today "$ASOF" 2>&1 | tail -3 | tee -a "$LOG"
SIM_INPUTS=sim/sep-inputs.json SIM_TAG=-sep python3 engine/messages.py >/dev/null
python3 engine/build_list.py >/dev/null
say "order-by, whatsapp, build list regenerated"

# 6 — site data (150 internal cross-checks; writes nothing if any fail)
cd site-sep
python3 scripts/gen-data.py 2>&1 | tail -6 | tee -a "$LOG"

# 7 — build, then refuse to publish if any real phone number reached the output
npm run build >/dev/null 2>&1 || { say "ABORT: next build failed"; exit 1; }
if grep -rqE '\+91[ -]?[6-9][0-9]{4}' .next/server data 2>/dev/null; then
  say "ABORT: a real phone number reached the build — not publishing"; exit 1
fi
say "build green, phone scan clean"

# 8 — publish
if [ "${DEPLOY:-1}" = "1" ]; then
  npx -y vercel deploy --prod --yes >/dev/null 2>&1 || { say "ABORT: deploy failed"; exit 1; }
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 25 https://jivo-mark2.vercel.app)
  [ "$code" = "200" ] || { say "ABORT: live site returned $code"; exit 1; }
  say "LIVE https://jivo-mark2.vercel.app ($code)"
else
  say "DEPLOY=0 — built locally, not published"
fi
say "=== refresh complete ==="
