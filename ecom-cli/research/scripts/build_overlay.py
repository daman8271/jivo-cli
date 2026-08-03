#!/usr/bin/env python3
"""Fold lens C's parameter extraction into a spec overlay.

Lens C emitted 541 parameter records with named path placeholders
(`/api/platform/{platform}/stats`); the spec pipeline keys everything on the
normalised form (`/api/platform/{}/stats`). This maps one onto the other and
keeps the ORIGINAL placeholder names, which are far better than anything
derived from the path text - `{table}` and `{card_code}` beat `{expiry_alert}`
and `{distributor}`.

Only `confidence: high|medium` records contribute an enum. A `low`-confidence
record still contributes the parameter NAME (knowing a param exists is useful)
but never a value set - publishing a guessed enum is how an operator ends up
sending a value nobody ever observed.
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(RUN, "harvest"))
from normalise import norm  # noqa: E402

TYPE_HINT = {
    "month": "integer", "year": "integer", "limit": "integer",
    "page": "integer", "page_size": "integer", "months": "integer",
    "no_paginate": "boolean", "active_only": "boolean",
    "respect_stock": "boolean", "upsert": "boolean",
}


def main():
    rows = [json.loads(l) for l in open(os.path.join(RUN, "harvest", "lensC-params.jsonl")) if l.strip()]
    overlay = collections.defaultdict(lambda: {"params": [], "path_param_names": []})
    wildcards = []

    for r in rows:
        p = r.get("path")
        if not p or not r.get("param"):
            if p and "*" in str(p):
                wildcards.append(r)
            continue
        if "*" in p:
            wildcards.append(r)
            continue
        key = norm(p)
        entry = {
            "name": r["param"],
            "type": TYPE_HINT.get(r["param"], "string"),
            "required": bool(r.get("required")),
            "description": "",
            "enum": [],
        }
        bits = []
        if r.get("format"):
            bits.append(str(r["format"]))
        if r.get("note"):
            bits.append(str(r["note"])[:180])
        entry["description"] = "; ".join(bits)[:240]
        # only a corroborated record may publish a value set
        if r.get("enum") and r.get("confidence") in ("high", "medium"):
            entry["enum"] = [str(x) for x in r["enum"]]
        overlay[key]["params"].append(entry)
        if r.get("kind") == "path":
            overlay[key]["path_param_names"].append(r["param"])

    # de-duplicate params per path, richest record wins
    out = {}
    for k, v in overlay.items():
        best = {}
        for pp in v["params"]:
            cur = best.get(pp["name"])
            if cur is None or (len(pp.get("enum") or []) > len(cur.get("enum") or [])) \
               or (len(pp.get("description") or "") > len(cur.get("description") or "")):
                best[pp["name"]] = pp
        out[k] = {"params": list(best.values()),
                  "path_param_names": list(dict.fromkeys(v["path_param_names"]))}

    json.dump(out, open(os.path.join(HERE, "lensc-overlay.json"), "w"), indent=1, sort_keys=True)
    print(f"{len(out)} paths carry overlay params ({sum(len(v['params']) for v in out.values())} params, "
          f"{sum(1 for v in out.values() for p in v['params'] if p['enum'])} with an enum)")
    print(f"{len(wildcards)} wildcard/global records held back for manual review:")
    for w in wildcards:
        print(f"   {w['path']:22} {w.get('param')}  {str(w.get('format'))[:70]}")


if __name__ == "__main__":
    main()
