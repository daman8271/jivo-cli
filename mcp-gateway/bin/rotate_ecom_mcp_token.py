#!/usr/bin/env python3
"""Keep the deployed jivo-ecom MCP JWT alive.

Adapted from rotate_factory_mcp_token.py. Two ecom-specific differences, both
of which will silently break a copy-paste of the factory version:

  * the refresh path is **/api/auth/refresh**, not the SimpleJWT default
    `/api/token/refresh/` and not `/api/auth/token/refresh` — that one 404s.
  * the ecom config.toml carries an extra `ecom_token` key that the MCP binary
    reads as the bearer for its typed-endpoint path. It must be rotated in
    lockstep with `access_token`, or the two halves of the server disagree
    about which credential is current.

POSTs the stored refresh token; SimpleJWT rotates the refresh token too, so
both the new access and the new refresh are written back. Run daily — well
inside the ~7-day refresh window — and auth self-sustains without the password
ever being stored.

Exit codes: 0 ok · 2 no config / no refresh_token · 3 refresh rejected
            (>7d lapse, needs a re-login) · 4 transport failure
            · 5 malformed response

Why this exists: the deployed ecom access token expired on 2026-07-23 and the
MCP served HTTP 401 for **eleven days**. Nothing rotated it, nothing noticed,
and the gateway reported `up: true` the whole time — because "up" only means
the backend answered tools/list, which a server with dead credentials does
perfectly well. The credentials are not consulted until a tool actually runs.
The config also had an EMPTY refresh_token, so it could not have self-healed
even if a rotator had existed.
"""
import datetime
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request

CONFIG = os.environ.get("ECOM_MCP_CONFIG", "/opt/jivo-mcp/env/ecom/config.toml")
URL = "https://ecom.jivo.in/api/auth/refresh"

# every key that must hold a current access token
ACCESS_KEYS = ("access_token", "ecom_token")


def read_key(text, key):
    m = re.search(rf"^{key}\s*=\s*['\"]([^'\"]*)['\"]", text, re.M)
    return m.group(1) if m else None


def replace_key(text, key, value, required=True):
    """Line-anchored substitution — must never span a key boundary."""
    pat = re.compile(rf"^({key}\s*=\s*).*$", re.M)
    if not pat.search(text):
        if required:
            raise SystemExit(f"key {key} absent from config; refusing to guess placement")
        return text
    return pat.sub(lambda m: f"{m.group(1)}'{value}'", text, count=1)


def main():
    if not os.path.isfile(CONFIG):
        print(f"no config at {CONFIG}", file=sys.stderr)
        return 2
    text = open(CONFIG).read()
    refresh = read_key(text, "refresh_token")
    if not refresh:
        print("no refresh_token in config — re-seed once with a live "
              "'auth login', then this rotator sustains it", file=sys.stderr)
        return 2

    req = urllib.request.Request(
        URL,
        data=json.dumps({"refresh": refresh}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        d = json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as e:
        print(f"refresh HTTP {e.code} — refresh token likely lapsed past 7 days. "
              f"Re-seed once with a live login, then this rotator sustains it.",
              file=sys.stderr)
        return 3
    except Exception as e:
        print(f"refresh failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 4

    access = d.get("access")
    if not access:
        print("refresh returned no access token", file=sys.stderr)
        return 5

    shutil.copy2(CONFIG, CONFIG + ".prev")
    for k in ACCESS_KEYS:
        text = replace_key(text, k, access, required=(k == "access_token"))
    if d.get("refresh"):
        text = replace_key(text, "refresh_token", d["refresh"])
    expiry = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
    expiry += datetime.timedelta(seconds=90000)
    text = re.sub(r"^(token_expiry\s*=\s*).*$",
                  lambda m: m.group(1) + expiry.replace(microsecond=0).isoformat(),
                  text, count=1, flags=re.M)

    tmp = CONFIG + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
    os.chmod(tmp, 0o600)
    os.replace(tmp, CONFIG)
    rotated = "yes" if d.get("refresh") else "no"
    print(f"ok — access rotated (keys: {', '.join(ACCESS_KEYS)}), "
          f"refresh rotated: {rotated}, "
          f"expires {expiry.replace(microsecond=0).isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
