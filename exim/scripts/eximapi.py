#!/usr/bin/env python3
"""Minimal authenticated client for eximbe.jivo.in. Reusable by crawlers + CLI prototyping."""

import json
import os
import urllib.request
import urllib.error
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEC = os.path.join(ROOT, ".secrets")


def _find_env():
    # Search upward from this CLI's root for the nearest .env holding EXIM_* creds
    # (works from both the old jivogpt/CLI/exim layout and the ~/jivo-cli/exim one).
    d = ROOT
    while True:
        cand = os.path.join(d, ".env")
        if os.path.isfile(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            raise FileNotFoundError("no .env found walking up from " + ROOT)
        d = parent


ENV = _find_env()


def _creds():
    d = {}
    for line in open(ENV):
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            d[k] = v
    return d


C = _creds()
API = C["EXIM_API"]
WEB = C["EXIM_WEB"]


def _tokfile():
    return json.load(open(os.path.join(SEC, "token.json")))


def login():
    body = json.dumps(
        {"email": C["EXIM_EMAIL"], "password": C["EXIM_PASSWORD"]}
    ).encode()
    req = urllib.request.Request(
        API + "/account/login/",
        data=body,
        headers={"Content-Type": "application/json", "Origin": WEB},
        method="POST",
    )
    d = json.loads(urllib.request.urlopen(req, timeout=30).read())
    json.dump(d, open(os.path.join(SEC, "token.json"), "w"))
    return d


def _refresh():
    tk = _tokfile()
    body = json.dumps({"refresh": tk["refresh"]}).encode()
    req = urllib.request.Request(
        API + "/account/login/refresh/",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    tk["access"] = json.loads(urllib.request.urlopen(req, timeout=30).read())["access"]
    json.dump(tk, open(os.path.join(SEC, "token.json"), "w"))


def get(path, params=None, _retry=True):
    """Authenticated GET. path like '/tank/', params dict. Returns (status, json_or_text)."""
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        tk = _tokfile()
    except Exception:
        login()
        tk = _tokfile()
    req = urllib.request.Request(
        url, headers={"Authorization": "Bearer " + tk["access"], "Origin": WEB}
    )
    try:
        r = urllib.request.urlopen(req, timeout=60)
        raw = r.read()
        try:
            return r.status, json.loads(raw)
        except Exception:
            return r.status, raw.decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code == 401 and _retry:
            _refresh()
            return get(path, params, _retry=False)
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw.decode("utf-8", "replace")


def ensure_token():
    """Return a valid access token, refreshing or re-logging-in as needed."""
    try:
        _tokfile()
        _refresh()  # cheap; rotates access from refresh
        return _tokfile()["access"]
    except Exception:
        return login()["access"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--token":
        print(ensure_token())
        sys.exit(0)
    p = sys.argv[1] if len(sys.argv) > 1 else "/tank/tank-summary/"
    prm = dict(kv.split("=", 1) for kv in sys.argv[2:]) if len(sys.argv) > 2 else None
    st, data = get(p, prm)
    print("HTTP", st)
    print(
        json.dumps(data, indent=2)[:2000]
        if isinstance(data, (dict, list))
        else str(data)[:2000]
    )
