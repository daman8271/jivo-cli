#!/usr/bin/env python3
"""Probe parameterised GET routes using ONLY observed identifier values.

READ-ONLY, GET only. Design constraints, all from skill rule 1:

  * Every substituted value came out of a live 200 response in this same run
    (see observed-ids.json). Nothing is invented, nothing is enumerated to
    "see what it accepts".
  * A path with no observed value for its parameter is SKIPPED and recorded
    as unprobeable. Unproven resolves to excluded, never to "probably fine".
  * Collection counts are snapshotted before and after, and every response is
    scanned for a created_at/updated_at inside the probe window, so a
    get_or_create that echoes its object back is caught. That is evidence of
    absence, not proof - it does not license loosening anything.

usage: probe_params.py <out-prefix>
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

SP = os.path.dirname(os.path.abspath(__file__))
BASE = "https://ecom.jivo.in"
TOKEN = json.load(open(os.path.join(SP, "token.json")))["access"]
OBS = json.load(open(os.path.join(SP, "observed-ids.json")))["ids"]
HARVEST = os.path.join(os.path.dirname(SP), "harvest")

# path -> ordered list of observed-id pools, one per {} in the path.
# A path absent from this map has no observed value and will be skipped.
POOLS = {
    "/api/chatbot/conversations/{}": ["chatbot_conversation_id"],
    "/api/uploads/{}": ["upload_id"],
    "/api/notifications/{}": ["notification_id"],
    "/api/dashboard/table-columns/{}": ["dashboard_table"],
    "/api/dashboard/table-count/{}": ["dashboard_table"],
    "/api/dashboard/table-data/{}": ["dashboard_table"],
    "/api/dashboard/expiry-alerts/{}": ["platform_slug"],
    "/api/dashboard/platform-expiry-alerts/{}/pos": ["platform_slug"],
    "/api/sap/distributors/{}": ["sap_card_code"],
    "/api/sap/distributor-invoices/{}": ["sap_card_code"],
    "/api/sap/distributor-orders/{}": ["sap_card_code"],
    "/api/sap/sales-invoices/{}": ["sap_card_code"],
    "/api/sap/sales-invoice-lines/{}": ["sap_doc_entry"],
    "/api/sap/platform-distributors/{}": ["platform_slug"],
}
# every /api/platform/{}/... route takes a platform slug in the first slot
PLATFORM_PREFIX = "/api/platform/{}/"

# collections whose size must not change across the run
WATCH = ["/api/chatbot/conversations", "/api/uploads", "/api/notifications",
         "/api/upload/master-sheet", "/api/upload/ads-master",
         "/api/upload/pincode-mapping"]

WINDOW_START = time.time()


def get(path):
    req = urllib.request.Request(BASE + path, method="GET", headers={
        "Authorization": f"Bearer {TOKEN}", "Accept": "application/json",
        "User-Agent": "jivo-cli-rescrape/1.0 (read-only endpoint survey)"})
    t0 = time.time()
    rec = {"path": path}
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            rec["http"] = r.status
            rec["bytes"] = len(raw)
            try:
                d = json.loads(raw)
                rec["top_type"] = "array" if isinstance(d, list) else "object"
                rec["sample_text"] = json.dumps(d)[:1200]
            except Exception:
                rec["top_type"] = "non-json"
                rec["sample_text"] = raw[:300].decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        rec["http"] = e.code
        rec["error"] = e.read()[:500].decode("utf-8", "replace")
    except Exception as e:
        rec["http"] = 0
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["ms"] = int((time.time() - t0) * 1000)
    return rec


def count_of(path):
    r = get(path)
    if r["http"] != 200:
        return None
    try:
        d = json.loads(r["sample_text"])
    except Exception:
        return r.get("bytes")
    return r.get("bytes")          # byte size is a fine change-detector here


def main():
    out_prefix = sys.argv[1]
    rec = json.load(open(os.path.join(HARVEST, "reconciled.json")))

    # observed platform slugs: live data first, bundle enum as corroboration
    slugs = OBS.get("platform_slug_from_expiry_alerts", [])
    OBS["platform_slug"] = slugs

    before = {p: count_of(p) for p in WATCH}
    print("watch snapshot (bytes):", before, flush=True)

    targets = []
    for p, v in sorted(rec.items()):
        if v["decision"] != "PROBE_SKIP_PARAM":
            continue
        if "GET" not in (v["methods"] or []) and not v["in_old_spec"]:
            continue
        pools = POOLS.get(p)
        if pools is None and p.startswith(PLATFORM_PREFIX) and p.count("{}") == 1:
            pools = ["platform_slug"]
        targets.append((p, pools))

    results, skipped = [], []
    for p, pools in targets:
        if not pools or any(not OBS.get(k) for k in pools):
            skipped.append({"path": p, "reason": "no observed value for its parameter"})
            continue
        vals = [str(OBS[k][0]) for k in pools]
        concrete, vi = p, 0
        while "{}" in concrete and vi < len(vals):
            concrete = concrete.replace("{}", vals[vi], 1)
            vi += 1
        if "{}" in concrete:
            skipped.append({"path": p, "reason": "more parameters than observed pools"})
            continue
        r = get(concrete)
        r["template"] = p
        r["substituted"] = vals
        results.append(r)
        print(f'  {r["http"]:>3} {concrete}', flush=True)
        time.sleep(0.15)

    after = {p: count_of(p) for p in WATCH}

    # did anything get created?
    changed = {p: (before[p], after[p]) for p in WATCH if before[p] != after[p]}
    ts_re = re.compile(r'"(?:created_at|updated_at)":\s*"([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9:.]+)')
    today = time.strftime("%Y-%m-%d")
    fresh = []
    for r in results:
        for m in ts_re.findall(r.get("sample_text", "")):
            if m.startswith(today):
                fresh.append({"path": r["path"], "ts": m})

    with open(f"{out_prefix}.jsonl", "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    json.dump({"skipped": skipped, "watch_before": before, "watch_after": after,
               "watch_changed": changed, "same_day_timestamps": fresh},
              open(f"{out_prefix}-audit.json", "w"), indent=1)

    from collections import Counter
    print("\n== status distribution ==", Counter(r["http"] for r in results))
    print(f"skipped (no observed value): {len(skipped)}")
    for s in skipped:
        print("   skip:", s["path"], "-", s["reason"])
    print("\n== CREATION CHECK ==")
    print("watched collections changed:", changed or "NONE")
    print("same-day created_at/updated_at in responses:", fresh or "NONE")


if __name__ == "__main__":
    main()
