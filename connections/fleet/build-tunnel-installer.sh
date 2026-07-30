#!/bin/sh
# Build the distributable installer by injecting the registrar private key into the
# template. The KEY IS A SECRET: the built .cmd must never be committed (.gitignore
# blocks it). Only the template lives in git.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
key=${JIVO_TUNNEL_REG_KEY:-$HOME/.ssh/jivo_tunnel_registrar}
plat=${1:-both}          # win | mac | both
outdir=${2:-$HOME/Downloads}
[ -f "$key" ] || { echo "missing registrar key: $key" >&2; exit 1; }
b64=$(base64 < "$key" | tr -d '\n')

build() {   # <template> <output>
  sed "s|@@REGKEY_B64@@|$b64|" "$1" > "$2"
  # Assert the artifact actually contains the key. A stale/failed substitution
  # produces a perfectly valid-looking file that can never authenticate.
  grep -q '@@REGKEY_B64@@' "$2" && { echo "substitution failed: $2" >&2; exit 1; }
  echo "built: $2"
}

[ "$plat" = win ] || [ "$plat" = both ] && build "$here/JIVO-VPS-TUNNEL.cmd.tpl" "$outdir/JIVO-VPS-TUNNEL.cmd"
if [ "$plat" = mac ] || [ "$plat" = both ]; then
  build "$here/JIVO-VPS-TUNNEL-MAC.command.tpl" "$outdir/JIVO-VPS-TUNNEL-MAC.command"
  chmod +x "$outdir/JIVO-VPS-TUNNEL-MAC.command"
fi
exit 0
