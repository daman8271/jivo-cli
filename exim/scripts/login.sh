#!/usr/bin/env bash
# Logs into eximbe.jivo.in, caches tokens to <exim>/.secrets/token.json
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/../../.env"   # jivogpt root .env holds EXIM_* creds
resp=$(curl -sS --max-time 30 -X POST "$EXIM_API/account/login/" \
  -H 'Content-Type: application/json' -H "Origin: $EXIM_WEB" \
  -d "{\"email\":\"$EXIM_EMAIL\",\"password\":\"$EXIM_PASSWORD\"}")
echo "$resp" > "$ROOT/.secrets/token.json"
python3 -c "import json;d=json.load(open('$ROOT/.secrets/token.json'));print('logged in as',d.get('name'),d.get('email'),'id',d.get('id'))"
