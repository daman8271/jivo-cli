#!/usr/bin/env python3
"""
How much of each JIVO web system does its CLI actually cover?

    python3 tools/coverage.py               # the table
    python3 tools/coverage.py factory       # + the per-domain breakdown and the missing list
    python3 tools/coverage.py --json

For every system this compares two things that already live in the repo:

  * the STUDY   — what a scrape of the app's own JS bundle (or Django urlconf) found
  * the SHIPPED — the endpoints the CLI's spec actually declares

and reports the difference.

WHY THIS FILE EXISTS
--------------------
On 2026-08-31 the same comparison was done by hand and reported 69 uncovered
factory endpoints. The real number was 32. The bug: the study writes a path
parameter as `{id}` while the spec writes it as `{barcode}`, so
`/barcode/lookup/{id}/` and `/barcode/lookup/{barcode}/` compared as different
endpoints and 29 already-shipped commands were counted as gaps. Every path on
both sides MUST go through canon() before being compared. That is the whole
point of this script — do not compare raw path strings anywhere.

Read-only. Touches no network and no business system.
"""

import json
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def canon(path):
    """The one normalisation both sides must agree on.

    Also collapses JS template slots (`${e}`) so a literal scraped from the
    bundle matches the same route written `{id}` in the spec.

    - percent-decode, so `%7Bid%7D` and `{id}` are the same endpoint
    - erase the parameter NAME, so `{id}` and `{barcode}` are the same slot
    - drop the trailing slash, so `/x/view` and `/x/view/` are one route
    """
    path = urllib.parse.unquote(path)
    path = re.sub(r"\$\{[^}]*\}", "{}", path)
    path = re.sub(r"\{[^}]*\}", "{}", path)
    return path.rstrip("/")


def load(rel):
    p = ROOT / rel
    if not p.exists():
        return None
    return json.loads(p.read_text())


def spec_paths(rel, key="resources"):
    """Pull every declared path out of a printing-press spec.yaml."""
    import yaml

    p = ROOT / rel
    if not p.exists():
        return {}
    doc = yaml.safe_load(p.read_text())
    found = {}

    def walk(node, group=None):
        if isinstance(node, dict):
            if isinstance(node.get("path"), str) and node["path"].startswith("/"):
                found[canon(node["path"])] = group
                return
            for k, v in node.items():
                walk(v, k if group is None else group)
        elif isinstance(node, list):
            for item in node:
                walk(item, group)

    walk(doc.get(key, {}))
    return found


# --- one loader per system -------------------------------------------------
# Each returns (studied, shipped, excluded)
#   studied  : {canon_path: domain}   READ-capable endpoints the study found
#   shipped  : {canon_path: group}    endpoints the CLI declares
#   excluded : {canon_path: reason}   deliberately not shipped


def factory():
    eps = load("factory-cli/research/endpoints-2026-08.json")["endpoints"]
    studied = {
        canon(e["path"]): e.get("domain", "?")
        for e in eps
        if "GET" in (e.get("methods") or [])
    }
    shipped = spec_paths("factory-cli/spec.yaml")
    kills = load("factory-cli/research/verdict-kills-2026-08.json") or []
    excluded = {canon(k): "killed by the 2026-08 study" for k in kills}
    return studied, shipped, excluded


def factory_live():
    """Denominator = the LIVE bundle sweep, not the 2026-08-03 study.

    Wider and fresher (935 paths vs 796) but verb-blind: the sweep reads string
    literals out of JS, so it cannot tell a read from a write. Roughly half of
    this surface is writes that a read-only CLI will never ship — so treat the
    percentage as a floor, and the per-prefix zeros as the real signal.
    """
    doc = load("factory-cli/research/live-api-2026-08-31.json")
    if not doc:
        return {}, {}, {}
    studied = {}
    for prefix, paths in doc["by_prefix"].items():
        for p in paths:
            studied[canon(p)] = prefix
    return studied, spec_paths("factory-cli/spec.yaml"), {}


def ecom():
    rec = load("ecom-cli/research/harvest/reconciled.json")
    studied = {
        canon(v["path"]): v.get("domain", "?")
        for v in rec.values()
        if v.get("get_capable")
    }
    shipped = spec_paths("ecom-cli/spec.yaml")
    excluded = {
        canon(v["path"]): "write endpoint"
        for v in rec.values()
        if not v.get("get_capable")
    }
    return studied, shipped, excluded


def oms():
    routes = load("oms-cli/research/harvest/urlconf-routes.json")["routes"]
    noise = lambda p: (
        "^media" in p or p.endswith("/admin/") or re.fullmatch(r"/api/[a-z-]+/", p)
    )
    studied = {canon(r["path"]): r.get("app", "?") for r in routes if not noise(r["path"])}
    shipped = spec_paths("oms-cli/oms-spec.yaml")
    # The urlconf dump carries no verbs, so writes cannot be separated here.
    return studied, shipped, {}


def exim():
    eps = load("exim/endpoints.json")["endpoints"]
    studied = {
        canon(e["path"]): e.get("category", "?") for e in eps if e.get("kind") == "read"
    }
    excluded = {
        canon(e["path"]): "write endpoint" for e in eps if e.get("kind") != "read"
    }
    oa = load("exim/cli/exim-openapi.json") or {"paths": {}}
    shipped = {canon(p): "exim" for p in oa["paths"]}
    return studied, shipped, excluded


SYSTEMS = {
    "factory": ("ji.jivo.in / factory.jivo.in", factory),
    "factory-live": ("ji.jivo.in (live sweep, verb-blind)", factory_live),
    "ecom": ("ecom.jivo.in", ecom),
    "oms": ("oms.jivo.in", oms),
    "exim": ("exim.jivo.in", exim),
}


def report(name):
    label, fn = SYSTEMS[name]
    studied, shipped, excluded = fn()
    covered = {p for p in studied if p in shipped}
    missing = {p: d for p, d in studied.items() if p not in shipped}
    deliberate = {p: excluded[p] for p in missing if p in excluded}
    real = {p: d for p, d in missing.items() if p not in excluded}
    pct = round(100 * len(covered) / len(studied)) if studied else 0
    return {
        "system": name,
        "host": label,
        "studied": len(studied),
        "covered": len(covered),
        "pct": pct,
        "missing": len(missing),
        "deliberately_excluded": len(deliberate),
        "real_gap": len(real),
        "_real": real,
        "_deliberate": deliberate,
    }


def pages_note():
    """Only exim has a page->endpoint map. Say so rather than implying otherwise."""
    pg = load("exim/pages.json")
    if not pg:
        return
    oa = load("exim/cli/exim-openapi.json") or {"paths": {}}
    cli = {canon(p) for p in oa["paths"]}
    full = sum(
        1
        for p in pg
        if p.get("endpoints") and all(canon(e) in cli for e in p["endpoints"])
    )
    print("\nPAGES")
    print(f"  exim    : {full}/{len(pg)} pages fully covered — the only system with a real")
    print("            page->endpoint map (exim/pages.json).")
    print("  factory : 420 routes across 25 sections, live-captured 2026-08-31")
    print("            (factory-cli/app-model/_route-map-2026-08-31.md). 8 sections have no")
    print("            CLI resource at all: warehouse-ops, etp, returns, fire,")
    print("            planning-purchase, finance, daily-tasks, sap-reports.")
    print("  ecom    : has a screen map (research/harvest/lensB-screen-map.md), not yet")
    print("            machine-joined to the spec.")
    print("  oms     : no page map at all. That, and joining ecom's, is the work still owed.")
    print("\n  `factory-live` compares against the full live sweep (935 paths) instead of")
    print("  the 2026-08-03 study (796). Wider and fresher, but verb-blind — see its docstring.")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    as_json = "--json" in sys.argv
    default = [n for n in SYSTEMS if n != "factory-live"]
    rows = [report(n) for n in (args or default)]

    if as_json:
        for r in rows:
            r.pop("_real"), r.pop("_deliberate")
        print(json.dumps(rows, indent=2))
        return

    print(f"{'system':10s} {'host':30s} {'studied':>8s} {'covered':>8s} {'%':>4s} "
          f"{'excl':>5s} {'GAP':>5s}")
    print("-" * 76)
    for r in rows:
        print(f"{r['system']:10s} {r['host']:30s} {r['studied']:8d} {r['covered']:8d} "
              f"{r['pct']:3d}% {r['deliberately_excluded']:5d} {r['real_gap']:5d}")

    if args:
        for r in rows:
            if not r["_real"]:
                continue
            print(f"\n--- {r['system']}: {len(r['_real'])} uncovered read endpoints ---")
            for p, d in sorted(r["_real"].items(), key=lambda kv: (kv[1], kv[0])):
                print(f"  {d:24s} {p}")
            if r["_deliberate"]:
                print(f"\n--- {r['system']}: {len(r['_deliberate'])} excluded on purpose ---")
                for p, why in sorted(r["_deliberate"].items()):
                    print(f"  {p:60s} {why}")
    else:
        pages_note()
        print("\nRun `python3 tools/coverage.py <system>` for the per-endpoint list.")


if __name__ == "__main__":
    main()
