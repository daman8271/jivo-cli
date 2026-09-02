#!/bin/bash
# usage: gst-prep.sh <N>  — logs out, opens login, fills creds for block N from the
# GST .env, writes a captcha png.
#
# SECURITY (Sentinel 2026-08-21): the password is fed to `browse` over STDIN via
# `chain`, never as an argv word. Argv is world-readable (`ps auxww`,
# /proc/<pid>/cmdline) and this repo is run on the shared VPS and the Mac Pro,
# not just one single-user Mac. Do not put "$P" back on a command line.
#
# NOTE: this script drives the portal through gstack `browse` with raw selectors
# and in-page fetch(). It is NOT covered by the Go client's read-only allowlist —
# line 21 below deliberately clicks Logout, which guard.go refuses outright. The
# read-only guarantee in ../cli/ is about the BINARY, not about this folder.
set -u
B="$HOME/.claude/skills/gstack/browse/dist/browse"
S=${GST_CAPTCHA_DIR:-/tmp}
N=$1
ENV=${GST_ENV:-$(cd "$(dirname "$0")/.." && pwd)/.env}
[ -r "$ENV" ] || { echo "cannot read $ENV (set \$GST_ENV)" >&2; exit 3; }

# Registration 03 (Punjab) has a KNOWN-BAD password (LOGIN-STATUS.md, rejected
# twice on 2026-08-21). Another attempt buys nothing and walks the account
# towards a department-cleared lockout in a filing month.
if [ "$N" = "03" ] || [ "$N" = "3" ]; then
  echo "refusing block 03 (Punjab): its password is known-bad. Get a corrected one from Accounts first." >&2; exit 4
fi

U=$(grep "^GST_${N}_USER=" "$ENV" | cut -d= -f2-)
P=$(grep "^GST_${N}_PASS=" "$ENV" | cut -d= -f2-)
ST=$(grep "^GST_${N}_STATE=" "$ENV" | cut -d= -f2-)
[ -n "$U" ] && [ -n "$P" ] || { echo "no GST_${N}_USER/PASS in $ENV" >&2; exit 3; }

$B js "(()=>{const a=Array.from(document.querySelectorAll('a')).find(a=>/^\s*Logout\s*$/i.test(a.innerText));if(a){a.click();return 'logout clicked'}return 'no logout link'})()" 2>/dev/null | grep -v UNTRUSTED
sleep 2
$B goto https://services.gst.gov.in/services/login >/dev/null 2>&1; $B wait --networkidle >/dev/null 2>&1

# credentials go in over stdin, one JSON array of [cmd, ...args]
U="$U" P="$P" python3 -c 'import json,os,sys; json.dump([["fill","#username",os.environ["U"]],["fill","#user_pass",os.environ["P"]],["press","Tab"]], sys.stdout)' \
  | $B chain >/dev/null 2>&1
unset P
sleep 2

$B js "(()=>{const i=document.getElementById('imgCaptcha');if(!i||!i.complete)return 'NOCAPTCHA';const c=document.createElement('canvas');c.width=i.naturalWidth*4;c.height=i.naturalHeight*4;c.getContext('2d').drawImage(i,0,0,c.width,c.height);return c.toDataURL('image/png').split(',')[1];})()" 2>/dev/null | grep -v UNTRUSTED | tr -d '\n' | base64 -d > $S/captcha$N.png 2>/dev/null
echo "prep $N ($ST / $U): $(file -b $S/captcha$N.png | cut -c1-40)"
