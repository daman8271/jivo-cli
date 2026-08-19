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

# Version stamp. An unversioned installer is why 2026-08-17 was hard to close out:
# three boxes already held an OLD copy of the .cmd, the old one prints an
# identical green OK while repairing nothing, so "it says OK" proved nothing.
# vN = how many commits have touched the Windows template (its real iteration
# count); the short SHA makes it exact. "+dirty" if built from uncommitted edits,
# because a build you cannot trace back to a commit must SAY so.
_n=$(git -C "$here" rev-list --count HEAD -- "$here/JIVO-VPS-TUNNEL.cmd.tpl" 2>/dev/null || echo 0)
_sha=$(git -C "$here" rev-parse --short HEAD 2>/dev/null || echo nogit)
_dirty=''
git -C "$here" diff --quiet -- "$here/JIVO-VPS-TUNNEL.cmd.tpl" "$here/JIVO-VPS-TUNNEL-MAC.command.tpl" 2>/dev/null || _dirty='+dirty'
ver="v${_n} (${_sha}${_dirty})"
echo "version: $ver"

build() {   # <template> <output>
  # Assert on the INPUT first. "The marker is gone from the output" passes just
  # as happily when the marker was never in the template to begin with — which
  # is exactly how the Mac installer shipped with no version at all from v1 to
  # v5 while this script printed "built:" every single time. A check that cannot
  # fail is not a check.
  grep -q '@@REGKEY_B64@@' "$1" || { echo "template has no @@REGKEY_B64@@ placeholder: $1" >&2; exit 1; }
  grep -q '@@VERSION@@'    "$1" || { echo "template has no @@VERSION@@ placeholder: $1" >&2; exit 1; }
  sed -e "s|@@REGKEY_B64@@|$b64|" -e "s|@@VERSION@@|$ver|" "$1" > "$2"
  # Assert the artifact actually contains the key. A stale/failed substitution
  # produces a perfectly valid-looking file that can never authenticate.
  grep -q '@@REGKEY_B64@@' "$2" && { echo "substitution failed: $2" >&2; exit 1; }
  # Same for the version: an installer that ships reporting "@@VERSION@@" is
  # worse than one with no version at all, because it looks deliberate.
  grep -q '@@VERSION@@' "$2" && { echo "version substitution failed: $2" >&2; exit 1; }
  # ...and that the real values landed. Absence of the placeholder is not
  # presence of the value.
  grep -qF "$ver" "$2" || { echo "version string missing from artifact: $2" >&2; exit 1; }
  grep -qF "$(printf %s "$b64" | cut -c1-40)" "$2" || { echo "registrar key missing from artifact: $2" >&2; exit 1; }
  echo "built: $2"
}

# This was `[ x = win ] || [ x = both ] && build ...`, which is correct — it
# groups as `(a || b) && c` — but reads like it might not, and the two platform
# arms were written in two different shapes. Checked in bash-posix and dash
# before changing it: same behaviour, so this is legibility, not a bug fix.
if [ "$plat" = win ] || [ "$plat" = both ]; then
  build "$here/JIVO-VPS-TUNNEL.cmd.tpl" "$outdir/JIVO-VPS-TUNNEL.cmd"
fi
if [ "$plat" = mac ] || [ "$plat" = both ]; then
  build "$here/JIVO-VPS-TUNNEL-MAC.command.tpl" "$outdir/JIVO-VPS-TUNNEL-MAC.command"
  chmod +x "$outdir/JIVO-VPS-TUNNEL-MAC.command"
fi
exit 0
