#!/usr/bin/env bash
# Authenticated GET. Usage: get.sh /path/ ['query=string']  -> prints JSON, auto-refreshes on 401
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/../../.env"   # jivogpt root .env holds EXIM_* creds
path="$1"; query="${2:-}"
tok(){ python3 -c "import json;print(json.load(open('$ROOT/.secrets/token.json'))['access'])"; }
rtok(){ python3 -c "import json;print(json.load(open('$ROOT/.secrets/token.json'))['refresh'])"; }
url="$EXIM_API$path"; [ -n "$query" ] && url="$url?$query"
do_get(){ curl -sS --max-time 45 -w '\n__HTTP_%{http_code}__' -H "Authorization: Bearer $(tok)" -H "Origin: $EXIM_WEB" "$url"; }
out=$(do_get)
code=$(echo "$out" | grep -oE '__HTTP_[0-9]+__' | grep -oE '[0-9]+')
if [ "$code" = "401" ]; then
  new=$(curl -sS --max-time 30 -X POST "$EXIM_API/account/login/refresh/" -H 'Content-Type: application/json' -d "{\"refresh\":\"$(rtok)\"}" | python3 -c "import sys,json;print(json.load(sys.stdin)['access'])")
  python3 -c "import json;d=json.load(open('$ROOT/.secrets/token.json'));d['access']='$new';json.dump(d,open('$ROOT/.secrets/token.json','w'))"
  out=$(do_get)
fi
echo "$out"
