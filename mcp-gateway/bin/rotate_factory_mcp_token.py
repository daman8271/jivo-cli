#!/usr/bin/env python3
"""Keep the deployed jivo-factory MCP JWT alive.

The MCP container mounts /opt/jivo-mcp/env/factory/config.toml, which uses the
Printing Press config format (access_token / refresh_token / token_expiry) —
NOT the ~/.config/jivo-factory/*.jwt files that factory-cli/bin/refresh_token.py
maintains. This rotator speaks the config.toml format.

POSTs the stored refresh token to /accounts/token/refresh/. SimpleJWT ROTATES
the refresh token, so both the new access AND the new refresh are written back.
Run daily — well inside the ~7-day refresh window — and auth self-sustains
without the password ever being stored.

Exit codes: 0 ok · 2 no config · 3 refresh rejected (>7d lapse, needs re-login)
            4 transport failure · 5 malformed response

Why this exists: the deployed token lapsed on 2026-07-24 and the MCP served
HTTP 401 for ten days. Nothing rotated it and nothing noticed, because the
health check only asserted that `initialize` returns 200 — which a server with
dead credentials still does.
"""
import datetime
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request

CONFIG = os.environ.get("FACTORY_MCP_CONFIG", "/opt/jivo-mcp/env/factory/config.toml")
URL = "https://factory.jivo.in/api/v1/accounts/token/refresh/"


def read_key(text, key):
    m = re.search(rf"^{key}\s*=\s*['\"]([^'\"]*)['\"]", text, re.M)
    return m.group(1) if m else None


def replace_key(text, key, value):
    """Line-anchored substitution — must never span an entry boundary."""
    pat = re.compile(rf"^({key}\s*=\s*).*$", re.M)
    if not pat.search(text):
        raise SystemExit(f"key {key} absent from config; refusing to guess placement")
    return pat.sub(lambda m: f"{m.group(1)}'{value}'", text, count=1)


def main():
    if not os.path.isfile(CONFIG):
        print(f"no config at {CONFIG}", file=sys.stderr)
        return 2
    text = open(CONFIG).read()
    refresh = read_key(text, "refresh_token")
    if not refresh:
        print("no refresh_token in config — needs a fresh 'auth login'", file=sys.stderr)
        return 2

    req = urllib.request.Request(
        URL,
        data=json.dumps({"refresh": refresh}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        d = json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as e:
        print(
            f"refresh HTTP {e.code} — refresh token likely lapsed past 7 days. "
            f"Re-seed once with a live login, then this rotator sustains it.",
            file=sys.stderr,
        )
        return 3
    except Exception as e:
        print(f"refresh failed: {type(e).__name__}: {e}", file=sys.stderr)
        return 4

    access = d.get("access")
    if not access:
        print("refresh returned no access token", file=sys.stderr)
        return 5

    shutil.copy2(CONFIG, CONFIG + ".prev")
    text = replace_key(text, "access_token", access)
    if d.get("refresh"):
        text = replace_key(text, "refresh_token", d["refresh"])
    expiry = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
    expiry += datetime.timedelta(seconds=90000)
    text = re.sub(
        r"^(token_expiry\s*=\s*).*$",
        lambda m: m.group(1) + expiry.replace(microsecond=0).isoformat(),
        text,
        count=1,
        flags=re.M,
    )

    tmp = CONFIG + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
    os.chmod(tmp, 0o600)
    os.replace(tmp, CONFIG)
    rotated = "yes" if d.get("refresh") else "no"
    print(f"ok — access rotated, refresh rotated: {rotated}, expires {expiry.replace(microsecond=0).isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
