#!/usr/bin/env python3
"""Lens D — the authoritative route list, straight from Django's own URLconf.

Lenses A/B/C read the SPA bundle, so they can only ever find routes the web app
CALLS. A route the server exposes but the current UI never touches is
structurally invisible to all three. That blind spot is not theoretical: it hid
`auth/party-product/add/`, `auth/users/{id}/delete/`, `devices/update/`,
`devices/me/`, and two whole apps (`einvoice`, `ewaybill`).

The OMS backend runs with `DEBUG = True` in production, so a request to a
non-existent path returns Django's 404 debug page, which lists **every pattern
in the resolver it reached** — names, converters and all. Requesting a bogus
path under each app root therefore yields that app's complete route table, for
free, with no token.

This is a defect in OMS (see FINDINGS-FOR-OMS-TEAM) and it will be fixed. When
it is, this lens stops working and the bundle lenses become the only source
again — so the output is snapshotted into research/harvest/ rather than being
re-derived on demand.

Read-only: issues GET to paths that deliberately do not exist. It cannot match
a real route, so it cannot touch data.

usage: enumerate_urlconf.py <out.json>
"""
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://oms.jivo.in"
BOGUS = "zzz-nonexistent-probe-path"

# app roots read from the project-level URLconf dump at /api/<bogus>/
APPS = ["auth", "orders", "sap", "hana", "sku", "service-layer", "einvoice",
        "ewaybill", "invoice", "legal", "tracker", "ui-config"]

LI = re.compile(r"<li>\s*(.*?)\s*</li>", re.S)
TAG = re.compile(r"<[^>]+>")
NAME = re.compile(r"\[name='([^']+)'\]")


def fetch(path):
    req = urllib.request.Request(BASE + path, headers={
        "Accept": "text/html",
        "User-Agent": "jivo-cli-rescrape/1.0 (read-only route survey)"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8", "replace")
    except Exception as e:
        print(f"  ! {path}: {type(e).__name__}", file=sys.stderr)
        return ""


def routes_from(page, prefix):
    """Each <li> is one pattern; the debug page splits an include() across
    several lines, so collapse whitespace before parsing."""
    out = []
    for raw in LI.findall(page):
        txt = html.unescape(TAG.sub(" ", raw))
        txt = re.sub(r"\s+", " ", txt).strip()
        if not txt:
            continue
        name = NAME.search(txt)
        pat = NAME.sub("", txt).strip()
        pat = re.sub(r"\s+", "", pat)
        if not pat or BOGUS in pat:
            continue
        if not pat.startswith("api/"):
            pat = prefix.lstrip("/") + pat
        out.append({"pattern": "/" + pat.lstrip("/"),
                    "name": name.group(1) if name else None})
    return out


def to_placeholder(pat):
    """Django converters -> spec placeholders. `<int:pk>` -> `{pk}`."""
    return re.sub(r"<(?:[a-z_]+:)?(\w+)>", r"{\1}", pat)


def main():
    allr, seen = [], set()
    for app in APPS:
        page = fetch(f"/api/{app}/{BOGUS}/")
        got = routes_from(page, f"/api/{app}/")
        n = 0
        for r in got:
            p = to_placeholder(r["pattern"])
            if p in seen:
                continue
            seen.add(p)
            allr.append({"path": p, "name": r["name"], "app": app})
            n += 1
        print(f"  {app:14} {n} routes", file=sys.stderr)
        time.sleep(0.15)

    allr.sort(key=lambda r: r["path"])
    json.dump({"source": "Django DEBUG 404 URLconf dump, oms.jivo.in, "
                         "read-only, no credentials",
               "count": len(allr), "routes": allr},
              open(sys.argv[1], "w"), indent=1)
    print(f"\n  {len(allr)} distinct routes -> {sys.argv[1]}", file=sys.stderr)


if __name__ == "__main__":
    main()
