#!/usr/bin/env bash
# Install / update the JIVO summon agent on the VPS. Idempotent — safe to re-run.
#
#   ssh vps 'bash -s' < summon/deploy/install-vps.sh
#
# What it puts in place:
#   /opt/jivo-summon/      the agent's home (workspace, queue, replies, audit)
#   jivo-summond.service   the receiver on 127.0.0.1:8710
#   3 tmux sessions        the REAL interactive claude sessions that answer
#   a Traefik file route   public HTTPS entry, obfuscated path + bearer token
#
# Traefik on this box runs with --network host, so it reaches 127.0.0.1 directly
# and no socat bridge container is needed (unlike the older jivo-webhook, which
# predates that).
set -euo pipefail

ROOT=/opt/jivo-summon
REPO=/root/jivo-cli
TRAEFIK_DYNAMIC=/docker/traefik/dynamic
PUBHOST=jivo-mcp.srv1685505.hstgr.cloud
PORT=8710

say() { printf '\n== %s\n' "$*"; }

say "preflight"
command -v tmux    >/dev/null || { apt-get update -qq && apt-get install -y -qq tmux; }
command -v claude  >/dev/null || { echo "FATAL: claude CLI not on PATH" >&2; exit 1; }
command -v python3 >/dev/null || { echo "FATAL: python3 not on PATH" >&2; exit 1; }
[ -d "$REPO" ] || { echo "FATAL: no jivo-cli checkout at $REPO" >&2; exit 1; }
[ -d "$TRAEFIK_DYNAMIC" ] || { echo "FATAL: no traefik dynamic dir at $TRAEFIK_DYNAMIC" >&2; exit 1; }

say "laying out $ROOT"
mkdir -p "$ROOT"/agent "$ROOT"/bin "$ROOT"/grants "$ROOT"/queue "$ROOT"/replies \
         "$ROOT"/workspace/.claude "$ROOT"/state/locks "$ROOT"/state/pending
chmod 700 "$ROOT"

# Code comes from the repo, so the agent always runs what is committed.
install -m 0755 "$REPO/summon/agent/pool.py"    "$ROOT/agent/pool.py"
install -m 0755 "$REPO/summon/agent/summond.py" "$ROOT/agent/summond.py"
install -m 0755 "$REPO/summon/bin/grantctl"     "$ROOT/bin/grantctl"
for g in "$REPO"/summon/grants/*; do
  [ -f "$g" ] && install -m 0755 "$g" "$ROOT/grants/$(basename "$g")"
done

# policy.json is operational state, and it is deliberately NOT in git (it carries
# hostnames, kit paths and SAP usernames; the repo is public). So it arrives
# out-of-band: scp it to /tmp/policy.json, or point SUMMON_POLICY_SRC at it.
#
# Install only if absent, so a hand-edit on the box — a new machine, a revoked
# grant, an auto-enrolled box — is never clobbered by a redeploy.
if [ ! -f "$ROOT/policy.json" ]; then
  SRC="${SUMMON_POLICY_SRC:-/tmp/policy.json}"
  if [ -f "$SRC" ]; then
    install -m 0600 "$SRC" "$ROOT/policy.json"
    echo "installed policy.json from $SRC"
    shred -u "$SRC" 2>/dev/null || rm -f "$SRC"
  elif [ -f "$REPO/summon/agent/policy.example.json" ]; then
    install -m 0600 "$REPO/summon/agent/policy.example.json" "$ROOT/policy.json"
    echo "WARNING: no real roster found — installed the EXAMPLE."
    echo "         It has no real boxes, so every summon will auto-enrol from scratch."
    echo "         scp the real policy.json to /tmp/policy.json and re-run."
  else
    echo "FATAL: no policy.json and no example to fall back on" >&2; exit 1
  fi
else
  echo "policy.json already present — left alone (it may hold auto-enrolled boxes)"
fi

install -m 0644 "$REPO/summon/agent/workspace-CLAUDE.md" "$ROOT/workspace/CLAUDE.md"

say "workspace allowlist"
# This is what lets a session act without a human at the keyboard while still
# being unable to do arbitrary damage. Root cannot use
# --dangerously-skip-permissions, so this allowlist IS the boundary: grantctl,
# plus read-only looking around. No bare ssh, no bare curl.
cat > "$ROOT/workspace/.claude/settings.json" <<'JSON'
{
  "permissions": {
    "allow": [
      "Bash(/opt/jivo-summon/bin/grantctl:*)",
      "Bash(cat /opt/jivo-summon/queue/*)",
      "Bash(cat /opt/jivo-summon/policy.json)",
      "Bash(python3 /root/jivo-cli/harness/bin/recall.py:*)",
      "Read(/opt/jivo-summon/**)",
      "Read(/root/jivo-cli/**)",
      "Write(/opt/jivo-summon/replies/**)",
      "Edit(/opt/jivo-summon/replies/**)"
    ],
    "deny": [
      "Bash(ssh:*)",
      "Bash(scp:*)",
      "Bash(rsync:*)",
      "Bash(curl:*)",
      "Bash(wget:*)",
      "Bash(git push:*)",
      "Read(/opt/jivo-summon/tokens.json)",
      "Read(/root/.claude.json)",
      "Read(/root/jivo-cli/env-vault/**)"
    ]
  }
}
JSON

say "tokens"
# One token per device. The token IS the device's identity; the daemon has no
# trust-the-header path.
if [ ! -f "$ROOT/tokens.json" ]; then
  python3 - "$ROOT" <<'PY'
import json, secrets, sys
from pathlib import Path

root = Path(sys.argv[1])
policy = json.loads((root / "policy.json").read_text())

tokens = {}
for box, b in policy.get("boxes", {}).items():
    if box == "vps":
        continue  # the host does not summon itself
    tokens[secrets.token_urlsafe(32)] = {
        "device": box,
        "operator": b.get("operator", "") or box,
        "ssh_alias": b.get("ssh_alias", box),
        "scopes": ["summon"],
    }
tokens[secrets.token_urlsafe(32)] = {
    "device": "daman-mac",
    "operator": "daman",
    "ssh_alias": "",
    "scopes": ["summon", "audit"],
}
p = root / "tokens.json"
p.write_text(json.dumps(tokens, indent=2))
p.chmod(0o600)
print("minted %d device tokens" % len(tokens))
PY
else
  echo "tokens.json already present — left alone (re-minting would lock every box out)"
fi
chmod 600 "$ROOT/tokens.json"

say "path slug"
# A random path slug so the endpoint is not guessable by crawlers. This is
# obscurity ON TOP OF the bearer token, never instead of it.
SLUG_FILE="$ROOT/state/path-slug"
if [ ! -f "$SLUG_FILE" ]; then
  python3 -c "import secrets;print('summon-'+secrets.token_hex(10))" > "$SLUG_FILE"
  chmod 600 "$SLUG_FILE"
fi
SLUG="$(cat "$SLUG_FILE")"

say "systemd unit"
cat > /etc/systemd/system/jivo-summond.service <<UNIT
[Unit]
Description=JIVO summon agent - the "Let's go" receiver
Documentation=https://github.com/daman8271/jivo-cli/tree/main/summon
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=${ROOT}
Environment=SUMMON_ROOT=${ROOT}
Environment=SUMMON_BIND=127.0.0.1
Environment=SUMMON_PORT=${PORT}
Environment=SUMMON_POOL_SIZE=3
Environment=PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/usr/bin/python3 ${ROOT}/agent/summond.py
Restart=always
RestartSec=5
UMask=0077
# The sessions it drives live in tmux and must outlive a unit restart.
KillMode=process

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now jivo-summond.service

say "traefik route"
python3 - "$TRAEFIK_DYNAMIC/jivo-summon.yml" "$PUBHOST" "$SLUG" "$PORT" <<'PY'
import sys
out, host, slug, port = sys.argv[1:5]
open(out, "w").write(f"""# JIVO summon agent. Traefik here runs --network host, so it dials the daemon's
# loopback port directly; no bridge container needed.
http:
  routers:
    jivo-summon:
      rule: "Host(`{host}`) && PathPrefix(`/{slug}`)"
      entryPoints: [websecure]
      middlewares: [jivo-summon-strip]
      service: jivo-summon
      tls:
        certResolver: letsencrypt
  middlewares:
    jivo-summon-strip:
      stripPrefix:
        prefixes: ["/{slug}"]
  services:
    jivo-summon:
      loadBalancer:
        servers:
          - url: "http://127.0.0.1:{port}"
""")
print("wrote", out)
PY
# providers.file.watch is on, so Traefik picks this up with no restart.

say "verifying"
sleep 4
if systemctl is-active --quiet jivo-summond.service; then
  echo "daemon: active"
else
  echo "daemon FAILED to start:"; journalctl -u jivo-summond -n 40 --no-pager; exit 1
fi

echo -n "loopback health: "
curl -fsS --max-time 10 "http://127.0.0.1:${PORT}/healthz" || { echo "FAILED"; exit 1; }
echo

echo -n "public health via traefik: "
for _ in 1 2 3 4 5 6; do
  if curl -fsS --max-time 12 "https://${PUBHOST}/${SLUG}/healthz"; then echo; break; fi
  sleep 4
done

echo "sessions:"
tmux ls 2>/dev/null | grep jivo-summon || echo "  (none yet — the daemon warms them at startup)"

cat <<INFO

======================================================================
 summon endpoint : https://${PUBHOST}/${SLUG}/v1/summon
 health          : https://${PUBHOST}/${SLUG}/healthz  (unauth, liveness only)
 audit log       : ${ROOT}/audit.jsonl
 watch it work   : ssh vps -t 'tmux attach -t jivo-summon-1'
 device tokens   : ${ROOT}/tokens.json  (0600, one per box)
======================================================================
INFO
