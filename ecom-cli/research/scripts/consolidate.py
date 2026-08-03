#!/usr/bin/env python3
"""Fold every probe run into one verdict per normalised path.

Precedence, strongest evidence first:
  200 anywhere            -> LIVE
  400 anywhere            -> LIVE_NEEDS_PARAMS (exists, GET works, param missing;
                             the body names the param, use it verbatim)
  500/503 everywhere      -> BROKEN_UPSTREAM (exclude, record the reason)
  403 everywhere          -> GATED (exists and is routed - a permission denial
                             is proof of existence, never proof of death)
  404 on EVERY slug tried -> DEAD
  404 on some, 200 on others -> LIVE_PARTIAL (view-level 404: available only
                             for the platforms that answered)
  not probed              -> UNPROBED (carry forward, do not infer)
"""
import collections
import json
import os
import sys

SP = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(SP), "harvest"))
from normalise import norm  # noqa: E402

HARVEST = os.path.join(os.path.dirname(SP), "harvest")

runs = []
for fn, kind in (("probe-run1.jsonl", "bare"),
                 ("probe-params.jsonl", "observed-id"),
                 ("probe-matched.jsonl", "slug-matched")):
    p = os.path.join(SP, fn)
    if os.path.exists(p):
        for l in open(p):
            r = json.loads(l)
            r["run"] = kind
            runs.append(r)

obs = collections.defaultdict(list)
for r in runs:
    tmpl = r.get("template") or r["path"]
    obs[norm(tmpl)].append(r)

verdict = {}
for path, rs in obs.items():
    codes = [r["http"] for r in rs]
    c = collections.Counter(codes)
    detail = {
        "path": path,
        "codes": dict(c),
        "attempts": [{"url": r["path"], "http": r["http"], "run": r["run"],
                      "slug": r.get("slug"),
                      "err": (r.get("error") or "")[:200]} for r in rs],
        "sample_shape": next((r.get("top_type") for r in rs if r["http"] == 200), None),
        "bytes": next((r.get("bytes") for r in rs if r["http"] == 200), None),
    }
    ok_slugs = sorted({r.get("slug") for r in rs if r["http"] == 200 and r.get("slug")})
    bad_slugs = sorted({r.get("slug") for r in rs if r["http"] == 404 and r.get("slug")})
    if 200 in c and 404 in c and ok_slugs:
        detail["status"] = "LIVE_PARTIAL"
        detail["available_for"] = ok_slugs
        detail["not_available_for"] = bad_slugs
    elif 200 in c:
        detail["status"] = "LIVE"
        if ok_slugs:
            detail["available_for"] = ok_slugs
    elif 400 in c:
        detail["status"] = "LIVE_NEEDS_PARAMS"
        detail["param_hint"] = next((r.get("error") for r in rs if r["http"] == 400), "")
    elif c and all(x in (500, 503) for x in codes):
        detail["status"] = "BROKEN_UPSTREAM"
        detail["reason"] = next((r.get("error") for r in rs if r["http"] in (500, 503)), "")
    elif c and all(x == 403 for x in codes):
        detail["status"] = "GATED"
        detail["reason"] = next((r.get("error") for r in rs if r["http"] == 403), "")
    elif c and all(x == 404 for x in codes):
        detail["status"] = "DEAD"
        detail["tried"] = bad_slugs or [r["path"] for r in rs]
    else:
        detail["status"] = "MIXED"
    verdict[path] = detail

rec = json.load(open(os.path.join(HARVEST, "reconciled.json")))
for p in rec:
    if p not in verdict:
        verdict[p] = {"path": p, "status": "UNPROBED", "codes": {},
                      "attempts": [], "sample_shape": None, "bytes": None}

json.dump(verdict, open(os.path.join(SP, "probe-verdicts.json"), "w"),
          indent=1, sort_keys=True)

c = collections.Counter(v["status"] for v in verdict.values())
print("== probe verdicts ==")
for k, v in sorted(c.items()):
    print(f"  {k:20} {v}")
print()
for k in ("DEAD", "BROKEN_UPSTREAM", "LIVE_PARTIAL", "MIXED"):
    hits = sorted(p for p, v in verdict.items() if v["status"] == k)
    if hits:
        print(f"-- {k} --")
        for p in hits:
            v = verdict[p]
            extra = v.get("available_for") or v.get("reason", "")[:110] or v.get("tried")
            print(f"   {p:52} {extra}")
        print()
