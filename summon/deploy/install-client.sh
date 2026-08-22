#!/usr/bin/env bash
# Put `letsgo` on this machine so it can reach JIVO's summon agent.
#
#   bash summon/deploy/install-client.sh <TOKEN>
#
# The token identifies this device to the agent. Only Daman can mint one — it
# lives in /opt/jivo-summon/tokens.json on the VPS. There is no self-enrolment,
# by design: the token IS the authorisation, so handing one out is the decision.
set -euo pipefail

TOKEN="${1:-}"
URL="${SUMMON_URL:-}"

if [ -z "$TOKEN" ]; then
  cat >&2 <<'USAGE'
usage: install-client.sh <TOKEN>

Get this box's token from Daman. On the VPS:
  python3 -c "import json;[print(k,v['device']) for k,v in json.load(open('/opt/jivo-summon/tokens.json')).items()]"

Optionally override the endpoint with SUMMON_URL=... (the default is read from
the VPS if this box can reach it by ssh).
USAGE
  exit 2
fi

# Discover the endpoint from the VPS rather than hardcoding the random path slug,
# which is regenerated per install and is not guessable on purpose.
if [ -z "$URL" ]; then
  if SLUG="$(ssh -o ConnectTimeout=10 -o BatchMode=yes vps \
              'cat /opt/jivo-summon/state/path-slug' 2>/dev/null)"; then
    URL="https://jivo-mcp.srv1685505.hstgr.cloud/${SLUG}/v1/summon"
    echo "discovered endpoint from the VPS"
  else
    echo "cannot reach the VPS by ssh to discover the endpoint." >&2
    echo "Ask Daman for the URL and re-run with SUMMON_URL=... " >&2
    exit 1
  fi
fi

CONF="$HOME/.jivo-summon.env"
umask 077
cat > "$CONF" <<CONFEOF
# JIVO summon agent — this device's credentials. Keep this file private.
# Minted by Daman; revoking means deleting this device's entry from
# /opt/jivo-summon/tokens.json on the VPS, not editing this file.
SUMMON_URL=$URL
SUMMON_TOKEN=$TOKEN
CONFEOF
chmod 600 "$CONF"
echo "wrote $CONF (0600)"

# Install the client somewhere already on PATH for interactive shells.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for d in "$HOME/.local/bin" "/usr/local/bin"; do
  if mkdir -p "$d" 2>/dev/null && [ -w "$d" ]; then
    install -m 0755 "$HERE/client/letsgo" "$d/letsgo"
    echo "installed $d/letsgo"
    case ":$PATH:" in
      *":$d:"*) ;;
      *) echo "NOTE: $d is not on your PATH — add it, or call $d/letsgo directly." ;;
    esac
    break
  fi
done

echo
echo "verifying…"
if "$(command -v letsgo || echo "$HOME/.local/bin/letsgo")" --status >/dev/null 2>&1; then
  echo "OK — the agent answered. Say: letsgo \"what you need\""
else
  echo "The client is installed but the agent did not answer."
  echo "Check the network, then run: letsgo --status"
  exit 1
fi
