#!/bin/bash
# usage: gst-submit.sh <N> <captcha>  — submits, prints who we are + returns snapshot
B="$HOME/.claude/skills/gstack/browse/dist/browse"; N=$1; C=$2
# Same refusal as gst-prep.sh: 03/Punjab's password is known-bad, and this script
# has no attempt counter of its own — a loop over it is a lockout.
if [ "$N" = "03" ] || [ "$N" = "3" ]; then
  echo "refusing block 03 (Punjab): its password is known-bad (LOGIN-STATUS.md). Never retry a credential rejection." >&2; exit 4
fi
$B network --clear >/dev/null 2>&1; $B fill "#captcha" "$C" >/dev/null 2>&1; $B click "button:has-text('Login')" >/dev/null 2>&1; sleep 4; $B wait --networkidle >/dev/null 2>&1
URL=$($B url 2>/dev/null); echo "--- LOGIN HTTP ---"; $B network 2>/dev/null | grep -iE "POST|authenticate|login|captcha|fowelcome" | grep -viE "static\.gst|\.js|\.css|\.png|\.html" | sed -E "s/ \([0-9]+ms, /(/" | head -8
if [[ "$URL" == *fowelcome* || "$URL" == *auth* ]]; then
  $B js "fetch('/services/api/ustatus').then(r=>r.json()).then(j=>'LOGIN OK  '+j.gstin+'  '+j.bname+'  state='+j.stcd+'  einv='+j.einvStatus+'  lastLogin='+j.Llogin)" 2>/dev/null | grep -v UNTRUSTED
  $B js "fetch('/returns/auth/api/filingsnapshot').then(r=>r.json()).then(j=>j.data.formNames.map(f=>f.formName+': '+f.retPrds.map(p=>p.monthYearName.replace(' - 20','-')+'='+p.filingStatus).join(', ')).join('\n'))" 2>/dev/null | grep -v UNTRUSTED
else
  echo "LOGIN FAILED → $URL"
  $B text 2>/dev/null | grep -iE 'invalid|incorrect|captcha|locked|error|not match|Enter valid|OTP' | head -5
fi
