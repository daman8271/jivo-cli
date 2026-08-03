#!/usr/bin/env python3
"""Decide the exact wire path for every endpoint, trailing slash included.

ecom's two path families have OPPOSITE trailing-slash conventions, verified
live on 2026-08-03 with redirects disabled:

    GET /api/shipment/shipments      -> 301  Location: /api/shipment/shipments/
    GET /api/shipment/shipments/     -> 403  (the real response, behind its gate)
    GET /api/dashboard/latest-month  -> 200
    GET /api/dashboard/latest-month/ -> 404

The shipped v0.1.0 spec has ZERO trailing slashes anywhere, so every shipment
command in it is served a 301 first. A GET client that follows redirects
survives that; it is still wrong, it costs a round trip, and it is proof those
paths were never exercised.

The normaliser deliberately strips trailing slashes so that two spellings of
the same endpoint compare equal - that is what makes the denylist and the
regression gate reliable. But the NORMALISED form must never be what gets
sent. This module maps each normalised key back to the exact spelling the
app's own client uses.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(RUN, "harvest"))
from normalise import norm  # noqa: E402


_QS_TAIL = re.compile(r"\$\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}$")


def canonical(norm_path, raw_paths):
    """Rebuild the wire path: normalised shape + the client's trailing slash.

    The subtlety that produced a wrong answer first time round: a trailing
    `${id}` is a PATH PARAMETER, and stripping it leaves a slash that then
    looks like a trailing slash. Only a trailing QUERY-STRING builder may be
    stripped - the same `` `? `` test the normaliser uses. Getting this wrong
    put a trailing slash on 19 paths that 404 with one:

        GET /api/sap/distributors/VENDA000526   -> 200
        GET /api/sap/distributors/VENDA000526/  -> 404

    Verified live: only the /api/shipment/ family wants the slash.
    """
    if not raw_paths:
        return norm_path
    trailing = False
    for raw in raw_paths:
        # Strip the trailing interpolation BEFORE splitting on '?'. Splitting
        # first truncates at the ternary operator inside the interpolation
        # itself - `${t ? `?${t}` : ``}` - leaving `/api/x/${t` and silently
        # losing the trailing slash on five shipment paths.
        base = raw
        m = _QS_TAIL.search(base)
        if m and ("`?" in m.group(0) or m.group(0).startswith("${?")):
            base = base[:m.start()]          # query-string builder only
        base = base.split("?", 1)[0]
        if base.endswith("/") and base.rstrip("/"):
            trailing = True
    return norm_path + "/" if trailing and norm_path != "/" else norm_path


def build():
    rec = json.load(open(os.path.join(RUN, "harvest", "reconciled.json")))
    out = {}
    for p, v in rec.items():
        out[p] = canonical(p, v.get("raw_paths") or [])
    return out


if __name__ == "__main__":
    m = build()
    json.dump(m, open(os.path.join(HERE, "canonical-paths.json"), "w"),
              indent=1, sort_keys=True)
    slashed = {k: v for k, v in m.items() if v.endswith("/")}
    print(f"{len(m)} paths; {len(slashed)} carry a trailing slash")
    import collections
    print("by domain:", collections.Counter(
        ([s for s in k.split("/") if s] + ["?"])[1] for k in slashed))
    for k in sorted(slashed):
        print("  ", slashed[k])
