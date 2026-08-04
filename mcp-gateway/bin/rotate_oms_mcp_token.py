#!/usr/bin/env python3
"""Keep the deployed jivo-oms MCP JWT alive.

Adapted from rotate_ecom_mcp_token.py. The OMS-specific differences — each of
which silently breaks a copy-paste of the ecom version:

  * the refresh path is **/api/auth/refresh/** WITH a trailing slash. OMS is
    Django and every route terminates in one. ecom's equivalent is
    `/api/auth/refresh` with no slash, and SimpleJWT's own default
    `/api/token/refresh/` is not routed here at all. Confirmed from the app's
    own bundle before this was written:
        Oa = [`/auth/login/`, `/auth/refresh/`, `/auth/logout/`]
        Ta.post(`${Ea}/auth/refresh/`, { refresh: e })     // Ea = ".../api"
  * there is no second bearer key. ecom's config carries `ecom_token` beside
    `access_token` and the two must move together; the OMS config has only
    `access_token` (its `token` and `auth_header` keys are empty and unused).
  * the OMS config quotes its values with SINGLE quotes. read_key/replace_key
    accept either, but do not "tidy" the file into double quotes — the Go
    config loader has only ever been exercised against what it writes itself.

POSTs the stored refresh token. SimpleJWT rotation is ON here — the response
carries a NEW refresh token as well as a new access token — so both are written
back. That detail is the whole point of running this daily: a rotator that
keeps re-presenting the ORIGINAL refresh token looks like it is working and
still dies the moment the original crosses its 7-day expiry.

Exit codes: 0 ok · 2 no config / no refresh_token · 3 refresh rejected
            (>7d lapse, needs a re-login) · 4 transport failure
            · 5 malformed response

Why this exists: the deployed OMS MCP served HTTP 401
`{"detail":"Given token not valid for any token type"}` on every tool call,
because BOTH its tokens had expired — access on 2026-07-24, refresh on
2026-07-30. Nothing rotated them and nothing noticed, because the gateway's
health check only proves the backend answers `tools/list`, which a server with
dead credentials does perfectly well. Credentials are not consulted until a
tool actually runs. With both tokens dead the config could not self-heal at
all and needed a fresh password login to re-seed.
"""
import datetime
import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.request

CONFIG = os.environ.get("OMS_MCP_CONFIG", "/opt/jivo-mcp/env/oms/config.toml")
URL = "https://oms.jivo.in/api/auth/refresh/"

# Every key that must hold a current access token. OMS has exactly one.
ACCESS_KEYS = ("access_token",)


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
        print("no refresh_token in config — re-seed once with a live login, "
              "then this rotator sustains it", file=sys.stderr)
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
        text = replace_key(text, k, access)
    if d.get("refresh"):
        text = replace_key(text, "refresh_token", d["refresh"])
    expiry = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=5, minutes=30)))
    expiry += datetime.timedelta(seconds=86400)      # OMS access TTL, measured
    text = re.sub(r"^(token_expiry\s*=\s*).*$",
                  lambda m: m.group(1) + expiry.replace(microsecond=0).isoformat(),
                  text, count=1, flags=re.M)

    tmp = CONFIG + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
    os.chmod(tmp, 0o600)
    os.replace(tmp, CONFIG)
    rotated = "yes" if d.get("refresh") else "no"
    print(f"ok — access rotated, refresh rotated: {rotated}, "
          f"expires {expiry.replace(microsecond=0).isoformat()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
