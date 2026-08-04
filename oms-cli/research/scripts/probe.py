#!/usr/bin/env python3
"""Live GET-probe of the JIVO OMS API.

READ-ONLY. Issues only GET. Never sends a mutating verb.

Differences from the factory/ecom probe, all forced by how OMS is built:

* base is https://oms.jivo.in and the harvested paths already carry /api.
* there is no Company-Code header. OMS's tenant selector is a QUERY PARAM,
  `?branch=`, appended by `Q6(url, branch)` in the bundle. Its values are
  `OIL` and `BEVERAGE`/`BEVERAGES`, read out of the app's own constants
  ($6/qfe/e8) — so sending them is inside skill rule 1 ("never send a parameter
  value you have not observed in a real payload or the app's own source"),
  not outside it. Pass 2 only ever sends those literal strings.
* Django trailing slashes. The app always calls with one; APPEND_SLASH means a
  call without one can 301-redirect or 404 depending on the route. We probe the
  form the app uses and record redirects rather than assuming uniformity.

The safety boundary, unchanged and not to be widened:
  - GET only, ever.
  - Skip parameterised paths ({...}) — no real id exists and inventing one is
    the exact incident this skill was written for.
  - Skip auth mutators and every path with write intent in the bundle.
  - Pass 1 sends NO query parameters at all. A bare 400 naming the missing
    param is the goal: it yields the contract verbatim without a guess.

usage: probe.py <paths-file> <out-prefix> [branch[,branch...]]
       paths-file: one absolute /api/... path per line
       branch:     omit for the bare pass; else OIL / BEVERAGE / BEVERAGES
"""
import json
import os
import queue
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

BASE = "https://oms.jivo.in"
TOKEN = open(os.environ.get("OMS_TOKEN_FILE", "/tmp/oms-rescrape/token.txt")).read().strip()
WORKERS = 5          # >6 makes these APIs refuse connections (skill rule 3)

# Paths the bundle shows being used to WRITE. A bare GET to them is probably
# harmless, but "probably" is what created six production rows on factory.
# Unproven resolves to excluded.
WRITE_INTENT = {
    "/api/auth/login/", "/api/auth/logout/", "/api/auth/refresh/",
    "/api/devices/register/",
    "/api/service-layer/invoice/",      # POSTs a document into SAP B1
    "/api/sku/upload/", "/api/legal/upload/",
    "/api/invoice/credit-limit/request/",
    "/api/invoice/pending/",
    "/api/sap/approve-sales-order/",
    "/api/tracker/jsap/sync/",
    "/api/tracker/actions/bulk/",
    "/api/orders/create/", "/api/orders/create-scheme/",
    "/api/orders/web-push/subscribe/",
    "/api/auth/assign-parties/", "/api/auth/assign-parties/bulk-upload/",
    "/api/auth/bulk-party/assign-products/", "/api/auth/party-product/bulk-add/",
    "/api/auth/party-product/remove/", "/api/auth/party-product/update-rate/",
    "/api/auth/remove-party/", "/api/auth/users/create/",
}


def shape(obj, depth=0):
    if depth > 2:
        return "..."
    if isinstance(obj, dict):
        return {k: shape(v, depth + 1) for k, v in list(obj.items())[:40]}
    if isinstance(obj, list):
        return [shape(obj[0], depth + 1)] if obj else []
    return type(obj).__name__


def rows_of(d):
    if isinstance(d, dict):
        for k in ("count", "total", "total_count"):
            if isinstance(d.get(k), int):
                return d[k]
        for k in ("results", "data", "items", "records"):
            if isinstance(d.get(k), list):
                return len(d[k])
        return None
    return len(d) if isinstance(d, list) else None


def probe(path, branch):
    url = BASE + path
    if branch:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode({"branch": branch})
    req = urllib.request.Request(url, method="GET", headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
        "User-Agent": "jivo-cli-rescrape/1.0 (read-only endpoint survey)",
    })
    rec = {"path": path, "branch": branch or ""}
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read()
            rec["http"] = r.status
            rec["bytes"] = len(raw)
            if r.geturl() != url:
                rec["redirected_to"] = r.geturl()
            try:
                d = json.loads(raw)
                rec["rows"] = rows_of(d)
                rec["shape"] = shape(d)
                rec["sample_text"] = json.dumps(d)[:1500]
                rec["json_top"] = type(d).__name__
            except Exception:
                rec["shape"] = "non-json"
                rec["sample_text"] = raw[:400].decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        rec["http"] = e.code
        rec["error"] = e.read()[:600].decode("utf-8", "replace")
    except Exception as e:
        # NOT an API fact — a transport failure. reprobe.py retries these
        # serially before any aggregate is computed (skill rule 3).
        rec["http"] = 0
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["ms"] = int((time.time() - t0) * 1000)
    return rec


def main():
    paths_file, out_prefix = sys.argv[1], sys.argv[2]
    branches = sys.argv[3].split(",") if len(sys.argv) > 3 else [""]

    paths = [l.strip() for l in open(paths_file) if l.strip().startswith("/")]
    skipped = {"parameterised": [], "write_intent": []}
    keep = []
    for p in paths:
        if "{" in p or "$" in p:
            skipped["parameterised"].append(p)
        elif p in WRITE_INTENT:
            skipped["write_intent"].append(p)
        else:
            keep.append(p)
    paths = sorted(set(keep))

    print(f"probing {len(paths)} paths x {len(branches)} branch value(s) "
          f"= {len(paths)*len(branches)} GETs, {WORKERS} workers")
    print(f"  skipped {len(skipped['parameterised'])} parameterised, "
          f"{len(skipped['write_intent'])} write-intent", flush=True)

    work = queue.Queue()
    for b in branches:
        for p in paths:
            work.put((p, b))

    results, lock, done = [], threading.Lock(), [0]
    total = work.qsize()

    def worker():
        while True:
            try:
                p, b = work.get_nowait()
            except queue.Empty:
                return
            r = probe(p, b)
            with lock:
                results.append(r)
                done[0] += 1
                if done[0] % 25 == 0:
                    print(f"  {done[0]}/{total}", flush=True)
            time.sleep(0.05)

    ts = [threading.Thread(target=worker, daemon=True) for _ in range(WORKERS)]
    [t.start() for t in ts]
    [t.join() for t in ts]

    with open(f"{out_prefix}.jsonl", "w") as f:
        for r in sorted(results, key=lambda r: (r["path"], r["branch"])):
            f.write(json.dumps(r) + "\n")
    json.dump(skipped, open(f"{out_prefix}-skipped.json", "w"), indent=1)

    print("\n== status distribution ==")
    for k, v in sorted(Counter(f'{r["branch"] or "-"}:{r["http"]}' for r in results).items()):
        print(f"  {k:22} {v}")
    print("\nrun reprobe.py before computing ANY aggregate (skill rule 3)")


if __name__ == "__main__":
    main()
