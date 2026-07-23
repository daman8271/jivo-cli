#!/usr/bin/env python3
"""
refresh_token.py — keep the Jivo Mart factory JWT alive non-interactively.

POSTs the stored refresh token to /accounts/token/refresh/. The server ROTATES
the refresh token, so we store BOTH the new access AND the new refresh (0600).
Run daily (well within the ~7-day refresh window) and auth self-sustains forever
without the password. If the refresh has expired (>7d gap), this fails non-zero
and the owner must re-seed once with: jivo-factory-pp-cli auth login.

Cardinal rule: never stores the password; only the rotating tokens, mode 0600.
"""

import json
import os
import sys
import urllib.request
import urllib.error

DIR = os.path.expanduser("~/.config/jivo-factory")
URL = "https://factory.jivo.in/api/v1/accounts/token/refresh/"


def main():
    rp = os.path.join(DIR, "refresh.jwt")
    if not os.path.isfile(rp):
        print("no refresh.jwt — run: jivo-factory-pp-cli auth login", file=sys.stderr)
        return 2
    refresh = open(rp).read().strip()
    body = json.dumps({"refresh": refresh}).encode()
    req = urllib.request.Request(
        URL, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        d = json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as e:
        print(
            f"refresh HTTP {e.code} (refresh token likely expired >7d) — owner re-seed: "
            f"jivo-factory-pp-cli auth login",
            file=sys.stderr,
        )
        return 3
    except Exception as e:
        print(f"refresh failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 4
    os.umask(0o077)
    wrote = []
    if d.get("access"):
        p = os.path.join(DIR, "access.jwt")
        open(p, "w").write(d["access"])
        os.chmod(p, 0o600)
        wrote.append("access")
    if d.get("refresh"):
        p = os.path.join(DIR, "refresh.jwt")
        open(p, "w").write(d["refresh"])
        os.chmod(p, 0o600)
        wrote.append("refresh(rotated)")
    if "access" not in wrote:
        print("refresh returned no access token", file=sys.stderr)
        return 5
    print(f"token refreshed: {', '.join(wrote)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
