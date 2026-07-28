#!/usr/bin/env bash
# Jivo Control Panel — login helper. Writes a fresh Django session cookie jar.
# Usage: ./login.sh   (reads creds from env or ../.env, falls back to defaults)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
[ -f "$here/../.env" ] && set -a && . "$here/../.env" && set +a
BASE="${JIVO_BASE:-http://103.89.45.75:9080}"
U="${JIVO_USER:?set JIVO_USER (put creds in ~/software/.env)}"
P="${JIVO_PASS:?set JIVO_PASS (put creds in ~/software/.env)}"
JAR="${JIVO_COOKIES:-$here/cookies.txt}"
LOGIN="$BASE/accounts/login/"
tmp="$(mktemp)"
curl -sS -m 30 -c "$JAR" "$LOGIN" -o "$tmp"
CSRF=$(grep -oE 'name="csrfmiddlewaretoken" value="[^"]*"' "$tmp" | head -1 | sed 's/.*value="//; s/"$//')
code=$(curl -sS -m 30 -c "$JAR" -b "$JAR" -e "$LOGIN" -H "Origin: $BASE" \
  --data-urlencode "csrfmiddlewaretoken=$CSRF" --data-urlencode "next=" \
  --data-urlencode "username=$U" --data-urlencode "password=$P" \
  -o /dev/null -w '%{http_code}' "$LOGIN")
rm -f "$tmp"
if [ "$code" = "302" ]; then echo "LOGIN OK ($U) -> $JAR"; else echo "LOGIN FAILED (HTTP $code)"; exit 1; fi
