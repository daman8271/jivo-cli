#!/usr/bin/env bash
# Jivo Control Panel — authenticated request helpers. SOURCE this file:
#   . ~/software/recon/jio.sh
#   jget  /realise/api/customer-master/
#   jpost /realise/api/sales-data/ '{"start_date":"2026-07-01","end_date":"2026-07-22"}'
# Re-login if a call returns HTML/login redirect:  bash ~/software/recon/login.sh
JIO_BASE="${JIVO_BASE:-http://103.89.45.75:9080}"
JIO_JAR="${JIVO_COOKIES:-$HOME/software/recon/cookies.txt}"
_jcsrf(){ grep -w csrftoken "$JIO_JAR" 2>/dev/null | tail -1 | awk '{print $NF}'; }
# jget PATH [extra-query] -> authenticated GET (XHR header)
jget(){ curl -sS -m 90 -b "$JIO_JAR" -H "X-Requested-With: XMLHttpRequest" -H "X-CSRFToken: $(_jcsrf)" "$JIO_BASE$1"; }
# jpost PATH JSON_BODY -> authenticated POST (JSON + CSRF)
jpost(){ local body="${2:-\{\}}"; curl -sS -m 120 -b "$JIO_JAR" -H "Content-Type: application/json" -H "X-Requested-With: XMLHttpRequest" -H "X-CSRFToken: $(_jcsrf)" --data "$body" "$JIO_BASE$1"; }
# jhead PATH -> just the status line + content type of a GET
jhead(){ curl -sS -m 60 -b "$JIO_JAR" -H "X-Requested-With: XMLHttpRequest" -o /dev/null -w 'HTTP %{http_code} | %{content_type} | %{size_download}b\n' "$JIO_BASE$1"; }
