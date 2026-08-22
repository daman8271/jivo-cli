#!/usr/bin/env python3
"""Re-seed the exim MCP backend's JWTs.

Companion to rotate_{ecom,oms,factory}_mcp_token.py. exim's differences:

  * Login is POST /account/login/ with {"email","password"} (not /auth/login/),
    and refresh is POST /account/login/refresh/ with {"refresh"}.
  * SimpleJWT rotation is ON, so a successful refresh returns a NEW refresh
    token too. Both are written back; keeping the original refresh token would
    look like it works right up until the 7-day window lapses.
  * exim's config carries no second bearer key - `token`, `auth_header`,
    `client_id` and `client_secret` are all empty and unused.

Why this script exists: on 2026-08-22 exim was found serving HTTP 401
("Given token not valid for any token type") to every agent call. Its access
token had expired on 2026-08-10 and the refresh token around 2026-08-16, so the
config could not self-heal and needed a password login. The gateway reported the
backend `up: true` throughout, because `up` only means MCP `initialize` returned
200 - it never calls a tool. Twelve days, silent. Same shape as the factory
401-for-ten-days incident (2026-07-24 -> 2026-08-03) and the OMS one before it.

Tries refresh first (cheap, no password), falls back to password login.
Never prints a token or a password.

Exit codes: 0 ok · 2 no config · 3 refresh AND login both rejected · 4 transport
"""
import base64, datetime, json, os, re, shutil, sys, urllib.error, urllib.request

CONFIG = sys.argv[1] if len(sys.argv) > 1 else "/opt/jivo-mcp/env/exim/config.toml"
ENVFILE = os.environ.get("EXIM_ENV_FILE", "/root/jivogpt/.env")


def post(url, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}
    except Exception as e:
        print(f"transport failure: {e}", file=sys.stderr)
        sys.exit(4)


def jwt_exp(tok):
    try:
        p = tok.split(".")[1]; p += "=" * (-len(p) % 4)
        exp = json.loads(base64.urlsafe_b64decode(p)).get("exp")
        return datetime.datetime.fromtimestamp(exp, datetime.timezone.utc) if exp else None
    except Exception:
        return None


def env_creds():
    if not os.path.exists(ENVFILE):
        print(f"no env file at {ENVFILE} - cannot password-login", file=sys.stderr)
        sys.exit(3)
    got = {}
    for line in open(ENVFILE):
        m = re.match(r'\s*(EXIM_EMAIL|EXIM_PASSWORD)\s*=\s*["\']?(.*?)["\']?\s*$', line)
        if m:
            got[m.group(1)] = m.group(2)
    if not {"EXIM_EMAIL", "EXIM_PASSWORD"} <= got.keys():
        print("EXIM_EMAIL / EXIM_PASSWORD missing from env file", file=sys.stderr)
        sys.exit(3)
    return got["EXIM_EMAIL"], got["EXIM_PASSWORD"]


if not os.path.exists(CONFIG):
    print(f"no config at {CONFIG}", file=sys.stderr); sys.exit(2)

src = open(CONFIG).read()

def val(key):
    m = re.search(rf"^{key}\s*=\s*['\"](.*?)['\"]", src, re.M)
    return m.group(1) if m else ""

base = (val("base_url") or "https://eximbe.jivo.in").rstrip("/")
refresh_tok = val("refresh_token")

access = new_refresh = None
how = None

if refresh_tok:
    code, body = post(f"{base}/account/login/refresh/", {"refresh": refresh_tok})
    if code == 200 and body.get("access"):
        access = body["access"]; new_refresh = body.get("refresh") or refresh_tok
        how = "refresh"
    else:
        print(f"  refresh rejected (HTTP {code}) - falling back to password login")

if not access:
    email, password = env_creds()
    code, body = post(f"{base}/account/login/", {"email": email, "password": password})
    if code != 200 or not body.get("access"):
        print(f"password login rejected (HTTP {code}): {str(body)[:200]}", file=sys.stderr)
        sys.exit(3)
    access = body["access"]; new_refresh = body.get("refresh") or refresh_tok
    how = "password login"

exp = jwt_exp(access)
shutil.copy2(CONFIG, CONFIG + ".prev")

out = re.sub(r"^access_token\s*=\s*.*$",  f"access_token = '{access}'",      src,  count=1, flags=re.M)
if new_refresh:
    out = re.sub(r"^refresh_token\s*=\s*.*$", f"refresh_token = '{new_refresh}'", out, count=1, flags=re.M)
if exp:
    out = re.sub(r"^token_expiry\s*=\s*.*$", "token_expiry = " + exp.astimezone().isoformat(), out, count=1, flags=re.M)

open(CONFIG, "w").write(out)
print(f"  re-seeded via {how}; access expires {exp.isoformat() if exp else 'unknown'}")
print(f"  backup: {CONFIG}.prev")
print("  next: docker compose restart exim, then call a REAL tool (initialize proves nothing)")
