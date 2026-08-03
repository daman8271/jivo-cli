#!/usr/bin/env python3
"""Live GET-probe of the JIVO ecom API. READ-ONLY.

Adapted from the jivo-rescrape skill's probe.py. Differences from factory:
  * single tenant - ecom has no Company-Code header
  * base is the SPA origin itself (https://ecom.jivo.in), paths already
    carry the /api prefix
  * SimpleJWT bearer, refreshed out of band

Safety boundary (unchanged, and it must stay unchanged):
  * GET only, never any other verb
  * skips parameterised paths - no real id, and inventing one is skill rule 1
  * skips auth mutators
  * sends NO query parameters at all; a bare 400 naming the missing param is
    the useful, safe result

usage: probe.py <paths-file> <out-prefix>
"""
import json
import os
import queue
import sys
import threading
import time
import urllib.error
import urllib.request

SP = os.path.dirname(os.path.abspath(__file__))
BASE = "https://ecom.jivo.in"
TOKEN = json.load(open(os.path.join(SP, "token.json")))["access"]
WORKERS = 4          # skill rule 3: <=6; refusals look exactly like "absent"

paths_file, out_prefix = sys.argv[1], sys.argv[2]

paths = [l.strip() for l in open(paths_file) if l.strip() and l.strip().startswith("/")]
paths = [p for p in paths if "{" not in p and "$" not in p]
paths = [p for p in paths if not any(p.rstrip("/").endswith(x) for x in (
    "/login", "/logout", "/change-password", "/refresh", "/token/refresh"))]
paths = sorted(set(paths))

print(f"probing {len(paths)} paths, {WORKERS} workers, GET only, no params", flush=True)


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
        for k in ("results", "data", "items", "records", "rows"):
            if isinstance(d.get(k), list):
                return len(d[k])
        return None
    return len(d) if isinstance(d, list) else None


def probe(path):
    url = BASE + path
    req = urllib.request.Request(url, method="GET", headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
        "User-Agent": "jivo-cli-rescrape/1.0 (read-only endpoint survey)",
    })
    rec = {"path": path}
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
            rec["http"] = r.status
            rec["bytes"] = len(raw)
            rec["ctype"] = r.headers.get("Content-Type", "")
            try:
                d = json.loads(raw)
                rec["rows"] = rows_of(d)
                rec["shape"] = shape(d)
                rec["top_type"] = "array" if isinstance(d, list) else (
                    "object" if isinstance(d, dict) else type(d).__name__)
                rec["sample_text"] = json.dumps(d)[:1500]
            except Exception:
                rec["shape"] = "non-json"
                rec["top_type"] = "non-json"
                rec["sample_text"] = raw[:400].decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        rec["http"] = e.code
        rec["error"] = e.read()[:600].decode("utf-8", "replace")
    except Exception as e:
        rec["http"] = 0                       # transport failure, NOT an API fact
        rec["error"] = f"{type(e).__name__}: {e}"
    rec["ms"] = int((time.time() - t0) * 1000)
    return rec


work = queue.Queue()
for p in paths:
    work.put(p)

results, lock, done = [], threading.Lock(), [0]
total = work.qsize()


def worker():
    while True:
        try:
            p = work.get_nowait()
        except queue.Empty:
            return
        r = probe(p)
        with lock:
            results.append(r)
            done[0] += 1
            if done[0] % 20 == 0:
                print(f"  {done[0]}/{total}", flush=True)
        time.sleep(0.12)


ts = [threading.Thread(target=worker, daemon=True) for _ in range(WORKERS)]
[t.start() for t in ts]
[t.join() for t in ts]

with open(f"{out_prefix}.jsonl", "w") as f:
    for r in sorted(results, key=lambda r: r["path"]):
        f.write(json.dumps(r) + "\n")

from collections import Counter  # noqa: E402
codes = Counter(r["http"] for r in results)
print("\n== status distribution ==")
for k, v in sorted(codes.items()):
    print(f"  {k:6} {v}")
live = sorted({r["path"] for r in results if r["http"] == 200})
open(f"{out_prefix}-live200.txt", "w").write("\n".join(live))
print(f"\nHTTP 200: {len(live)} -> {out_prefix}-live200.txt")
print(f"transport failures (http=0, MUST reprobe): {codes.get(0, 0)}")
