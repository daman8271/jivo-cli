#!/usr/bin/env python3
"""
Phase B — lossless capture of all Jivo Mart (JIVO_MART) factory data.

Pulls every verified GET-200 endpoint (research/get200.txt) in full, following
DRF pagination (?page / next), and writes the raw payload per endpoint to
raw/<slug>.json plus a manifest. Read-only; same auth + scope the CLI uses
(Authorization: Bearer <token>, Company-Code: JIVO_MART). Deterministic — no LLM.
"""

import json
import os
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

ROOT = "/root/jivo-factory-intel"
RAW = os.path.join(ROOT, "raw")
os.makedirs(RAW, exist_ok=True)
TOKEN = open(os.path.expanduser("~/.config/jivo-factory/access.jwt")).read().strip()
BASE = "https://factory.jivo.in/api/v1"
HDR = {"Authorization": f"Bearer {TOKEN}", "Company-Code": "JIVO_MART"}
eps = [
    line.strip()
    for line in open(os.path.join(ROOT, "research/get200.txt"))
    if line.strip()
]


def slug(ep):
    return ep.strip("/").replace("/", "__") or "root"


MAX_RECORDS = 60000  # safety ceiling per endpoint


def get(url):
    req = urllib.request.Request(url, headers=HDR)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def fetch_all(ep):
    sep = "&" if "?" in ep else "?"
    # Probe DRF paginated mode first: ?page=1 flips capped bare-lists into a
    # {count,next,results} envelope we can walk fully.
    try:
        first = get(BASE + ep + sep + "page=1&page_size=100")
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            first = None  # endpoint rejects ?page -> fall back to plain
        else:
            return ep, {"kind": "http_error", "status": e.code, "count": 0}
    except Exception as e:
        return ep, {"kind": "error", "error": type(e).__name__, "count": 0}

    if (
        isinstance(first, dict)
        and isinstance(first.get("results"), list)
        and ("count" in first or "next" in first)
    ):
        items = list(first["results"])
        count = first.get("count")
        nxt = first.get("next")
        page = 1
        capped = False
        while nxt or (count is not None and len(items) < count):
            page += 1
            try:
                j = get(BASE + ep + sep + f"page={page}&page_size=100")
            except Exception:
                break
            res = j.get("results") if isinstance(j, dict) else None
            if not res:
                break
            items.extend(res)
            nxt = j.get("next") if isinstance(j, dict) else None
            if len(items) >= MAX_RECORDS:
                capped = True
                break
            if page > 3000:
                break
        kind = "paginated_list"
        data = items
        meta_extra = {"pages": page, "reported_count": count, "truncated": capped}
    else:
        # Not paginated by ?page: plain GET (bare list or object).
        try:
            j = get(BASE + ep)
        except urllib.error.HTTPError as e:
            return ep, {"kind": "http_error", "status": e.code, "count": 0}
        except Exception as e:
            return ep, {"kind": "error", "error": type(e).__name__, "count": 0}
        data = j
        if isinstance(j, list):
            kind = "list"
            # round-number bare lists with no pagination = likely a hard server cap
            meta_extra = {"pages": 1, "hard_capped": len(j) in (100, 200, 500, 1000)}
        else:
            kind = "object"
            meta_extra = {"pages": 1}

    count = len(data) if isinstance(data, list) else (1 if data is not None else 0)
    out = os.path.join(RAW, slug(ep) + ".json")
    with open(out, "w") as f:
        json.dump(
            {"endpoint": ep, "kind": kind, "count": count, "data": data},
            f,
            ensure_ascii=False,
        )
    return ep, {
        "kind": kind,
        "count": count,
        "file": os.path.basename(out),
        **meta_extra,
    }


print(f"capturing {len(eps)} endpoints -> {RAW}", flush=True)
manifest = {}
with ThreadPoolExecutor(max_workers=8) as ex:
    for ep, meta in ex.map(fetch_all, eps):
        manifest[ep] = meta
        print(f"  {meta.get('count', 0):>6}  [{meta['kind']}]  {ep}", flush=True)

with open(os.path.join(ROOT, "raw", "_manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

total_records = sum(
    m.get("count", 0)
    for m in manifest.values()
    if m.get("kind") in ("list", "paginated_list")
)
errs = [e for e, m in manifest.items() if m["kind"] in ("error", "http_error")]
print(
    f"\nDONE. endpoints={len(manifest)} total_records={total_records} errors={len(errs)}",
    flush=True,
)
if errs:
    print("errors:", errs[:20], flush=True)
