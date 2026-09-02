#!/bin/sh
# SAP B1 full client from a Mac (or Linux) — RDP to the Windows app box (Jivo-App1)
# through the always-on hanadb reverse tunnel. No VPN, works from any network.
#
#   ./connections/sap-rdp-mac.sh          # opens the tunnel + launches Windows App
#
# RDP login = the Windows box credentials (JIVOAPP_RDP in connections/fleet-access.env).
# The SAP B1 client on that box logs in with your normal SAP user.
# Linux: use any RDP client (Remmina/FreeRDP) against localhost:13389 after the tunnel line.

set -e

# refresh the tunnel (idempotent)
pkill -f '13389:10.10.101.52:13579' 2>/dev/null || true
ssh -f -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L 13389:10.10.101.52:13579 jivo-sap-new

echo "RDP tunnel live: localhost:13389 -> Jivo-App1 (10.10.101.52:13579)"

# hand off to the Windows App (Mac). On Linux, run: xfreerdp /v:localhost:13389
if [ "$(uname)" = "Darwin" ]; then
  open "rdp://full%20address=s:localhost:13389" 2>/dev/null \
    || open -a "Windows App" 2>/dev/null \
    || echo "Install 'Windows App' (Mac App Store or: brew install --cask windows-app), then connect to localhost:13389"
fi
