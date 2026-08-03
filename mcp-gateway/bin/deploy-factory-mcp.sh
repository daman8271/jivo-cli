#!/usr/bin/env bash
# Build and deploy the jivo-factory MCP server to the VPS gateway.
#
# The container at /opt/jivo-mcp mounts ./bin/factory-mcp read-only and serves it
# behind Traefik at PathPrefix(/mcp-<pathbase>/factory). Deploying is therefore:
# replace the binary, restart the service, prove a real tool call works.
#
# Deliberately NOT a blind restart: the gateway's existing health check only
# asserts that MCP `initialize` returns 200, which a server with dead credentials
# also does — that is how the factory server served HTTP 401 for ten days
# unnoticed (2026-07-24 → 2026-08-03). This script verifies by calling a tool.
#
# usage: deploy-factory-mcp.sh [--no-build]
set -euo pipefail

REPO_CLI="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../factory-cli" && pwd)"
REMOTE=vps
REMOTE_DIR=/opt/jivo-mcp
BASE_URL="https://jivo-mcp.srv1685505.hstgr.cloud"
PATHBASE="${JIVO_MCP_PATHBASE:-mcp-0c9a3015a3ae56ca21b7}"
BIN=/tmp/factory-mcp.linux-amd64

if [ "${1:-}" != "--no-build" ]; then
  echo "==> building cmd/jivo-factory-pp-mcp for linux/amd64 (VPS is x86_64)"
  ( cd "$REPO_CLI" && CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
      go build -trimpath -ldflags "-s -w" -o "$BIN" ./cmd/jivo-factory-pp-mcp )
  ls -la "$BIN" | awk '{printf "    built %.1f MB\n", $5/1048576}'
fi

echo "==> GET-only guard must hold before anything ships (patch 0003)"
( cd "$REPO_CLI" && go test ./internal/mcp/... 2>&1 | tail -5 )

echo "==> backing up the live binary to .prev"
ssh "$REMOTE" "cp -a $REMOTE_DIR/bin/factory-mcp $REMOTE_DIR/bin/factory-mcp.prev"

echo "==> uploading"
scp -q "$BIN" "$REMOTE:$REMOTE_DIR/bin/factory-mcp.new"
ssh "$REMOTE" "chmod 0755 $REMOTE_DIR/bin/factory-mcp.new && mv $REMOTE_DIR/bin/factory-mcp.new $REMOTE_DIR/bin/factory-mcp"

echo "==> restarting the factory service"
ssh "$REMOTE" "cd $REMOTE_DIR && docker compose restart factory >/dev/null 2>&1"
sleep 5

echo "==> verifying with a REAL tool call (not just initialize)"
U="$BASE_URL/$PATHBASE/factory/mcp"
H=$(mktemp)
curl -s --max-time 25 -D "$H" -o /dev/null -X POST "$U" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"deploy","version":"1"}}}'
SID=$(grep -i '^mcp-session-id:' "$H" | tr -d '\r' | awk '{print $2}')
if [ -z "$SID" ]; then echo "FAIL: no session id from initialize"; exit 1; fi
curl -s --max-time 25 -o /dev/null -X POST "$U" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" -H "mcp-session-id: $SID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'

TOOLS=$(curl -s --max-time 30 -X POST "$U" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" -H "mcp-session-id: $SID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}')
echo "    tools exposed: $(printf '%s' "$TOOLS" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["result"]["tools"]))')"

RES=$(curl -s --max-time 40 -X POST "$U" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" -H "mcp-session-id: $SID" \
  -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"jivo-factory_execute","arguments":{"endpoint_id":"accounts.me","params":{}}}}')

if printf '%s' "$RES" | grep -q '"isError":true'; then
  echo "FAIL: live tool call errored —"
  printf '%s\n' "$RES" | head -c 400
  echo
  echo "ROLLING BACK to factory-mcp.prev"
  ssh "$REMOTE" "mv $REMOTE_DIR/bin/factory-mcp.prev $REMOTE_DIR/bin/factory-mcp && cd $REMOTE_DIR && docker compose restart factory >/dev/null 2>&1"
  exit 1
fi

echo "    live tool call OK"
echo "==> deployed. Connector URL: $BASE_URL/$PATHBASE/jivo/mcp (unified gateway)"
rm -f "$H"
