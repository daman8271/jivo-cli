#!/usr/bin/env python3
"""
vercel-public — remove Vercel Authentication / Password Protection so deployments are public.

Vercel has NO team-wide "default off" setting: every NEW project starts with
ssoProtection = all_except_custom_domains (the login gate on deployment/preview URLs).
This script disables that gate. It is idempotent and safe to re-run.

Usage:
    vercel-public.py                 # open ALL projects on the team
    vercel-public.py myproj otherp   # open only the named projects
    vercel-public.py --dry-run       # show what would change, change nothing

Token: read from the Vercel CLI login (~/Library/Application Support/com.vercel.cli/auth.json).
Run `vercel login` first if it's expired.
Team: defaults to $VERCEL_TEAM_ID or the known team; override with VERCEL_TEAM_ID.
"""
import json, os, sys, urllib.request, urllib.error

# The CLI stores its token in a platform-specific place. macOS uses
# Application Support; Linux (the VPS that runs the live refresh) uses the XDG
# data dir. Take the first that exists, so one copy of this script serves both.
_AUTH_CANDIDATES = [
    "~/Library/Application Support/com.vercel.cli/auth.json",   # macOS
    "~/.local/share/com.vercel.cli/auth.json",                  # Linux / XDG
    "~/.config/com.vercel.cli/auth.json",
]
AUTH = next((p for p in map(os.path.expanduser, _AUTH_CANDIDATES) if os.path.exists(p)),
            os.path.expanduser(_AUTH_CANDIDATES[0]))
TEAM = os.environ.get("VERCEL_TEAM_ID", "team_3bO4LBGqtjj9U2vRkwmHdpn3")

def token():
    try:
        return json.load(open(AUTH))["token"]
    except Exception as e:
        sys.exit("Could not read Vercel token (%s). Run `vercel login` first." % e)

def api(method, path, tok, body=None):
    url = "https://api.vercel.com" + path
    data = json.dumps(body).encode() if body is not None else None
    h = {"Authorization": "Bearer " + tok}
    if data: h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    return json.load(urllib.request.urlopen(req))

def all_projects(tok):
    base = "/v9/projects?teamId=%s&limit=100" % TEAM
    url, out = base, []
    while url:
        d = api("GET", url, tok)
        out += d.get("projects", [])
        nxt = d.get("pagination", {}).get("next")
        url = (base + "&until=%s" % nxt) if nxt else None
    return out

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    dry  = "--dry-run" in sys.argv
    tok  = token()
    # validate token early
    try:
        u = api("GET", "/v2/user", tok)
        who = (u.get("user") or u).get("email")
    except urllib.error.HTTPError as e:
        sys.exit("Token rejected (HTTP %s). Run `vercel login`." % e.code)
    projs = all_projects(tok)
    if args:
        want = set(args)
        projs = [p for p in projs if p["name"] in want or p["id"] in want]
        missing = want - {p["name"] for p in projs} - {p["id"] for p in projs}
        if missing: print("⚠ not found:", ", ".join(sorted(missing)))
    print("Account %s · team %s · %d project(s) in scope%s\n" % (who, TEAM, len(projs), "  [DRY RUN]" if dry else ""))
    changed = skip = fail = 0
    for p in projs:
        gated = bool(p.get("ssoProtection") or p.get("passwordProtection"))
        if not gated:
            skip += 1; continue
        if dry:
            print("  would open:", p["name"]); changed += 1; continue
        try:
            r = api("PATCH", "/v9/projects/%s?teamId=%s" % (p["id"], TEAM), tok,
                    {"ssoProtection": None, "passwordProtection": None})
            if r.get("ssoProtection") or r.get("passwordProtection"):
                fail += 1; print("  STILL GATED:", p["name"])
            else:
                changed += 1; print("  opened:", p["name"])
        except urllib.error.HTTPError as e:
            fail += 1; print("  FAILED:", p["name"], e.code, e.read()[:120])
    verb = "would open" if dry else "opened"
    print("\n%s: %d · already-public: %d · failed: %d" % (verb, changed, skip, fail))
    sys.exit(1 if fail else 0)

if __name__ == "__main__":
    main()
