#!/usr/bin/env python3
"""
Close the completeness gaps the two auditors found:
  - person_gatein: entries, visitors, labours, contractors, person-types, gates  (MISSED domain)
  - company/companies/                                                            (MISSED master)
  - gate-core/sales-dispatch/documents/  -> bust the 200-cap with ?limit= (true 1,130)
  - barcode/items/oitm/                  -> enumerate ?search=FG0000{1..4} (true ~425, default caps 200)
  - quality-control/sap-items + production-execution/sap/items -> search-proxies (sampled + noted)
Writes/overwrites raw/<slug>.json in the standard {endpoint,kind,count,data} shape so the
renderer picks them up. Read-only against the live API; same auth + JIVO_MART scope.
"""

import json
import os
import urllib.request
import urllib.error
import urllib.parse

ROOT = "/root/jivo-factory-intel"
RAW = os.path.join(ROOT, "raw")
A = open(os.path.expanduser("~/.config/jivo-factory/access.jwt")).read().strip()
BASE = "https://factory.jivo.in/api/v1"
HDR = {"Authorization": f"Bearer {A}", "Company-Code": "JIVO_MART"}


def slug(ep):
    return ep.strip("/").replace("/", "__") or "root"


def get(path):
    req = urllib.request.Request(BASE + path, headers=HDR)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def paginate(ep):
    """Full DRF pagination via ?page (same logic as capture.py)."""
    sep = "&" if "?" in ep else "?"
    try:
        first = get(ep + sep + "page=1&page_size=100")
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            first = None
        else:
            raise
    if (
        isinstance(first, dict)
        and isinstance(first.get("results"), list)
        and ("count" in first or "next" in first)
    ):
        items = list(first["results"])
        page = 1
        while first.get("next") or (first.get("count") and len(items) < first["count"]):
            page += 1
            j = get(ep + sep + f"page={page}&page_size=100")
            res = j.get("results") if isinstance(j, dict) else None
            if not res:
                break
            items.extend(res)
            first = j
            if page > 2000:
                break
        return "paginated_list", items
    j = get(ep)
    return ("list", j) if isinstance(j, list) else ("object", j)


def save(ep, kind, data):
    cnt = len(data) if isinstance(data, list) else (1 if data is not None else 0)
    json.dump(
        {"endpoint": ep, "kind": kind, "count": cnt, "data": data},
        open(os.path.join(RAW, slug(ep) + ".json"), "w"),
        ensure_ascii=False,
    )
    print(f"  {cnt:>6}  [{kind}]  {ep}")
    return cnt


results = {}
print("=== person_gatein (missed domain) + company (missed master) ===")
for ep in [
    "/person-gatein/entries/",
    "/person-gatein/visitors/",
    "/person-gatein/labours/",
    "/person-gatein/contractors/",
    "/person-gatein/person-types/",
    "/person-gatein/gates/",
    "/company/companies/",
]:
    try:
        kind, data = paginate(ep)
        results[ep] = save(ep, kind, data)
    except Exception as e:
        print(f"  ERR {ep}: {type(e).__name__}")

print("=== sales-dispatch/documents — bust the 200-cap with ?limit= ===")
ep = "/gate-core/sales-dispatch/documents/"
j = get(ep + "?limit=100000")
data = j if isinstance(j, list) else j.get("results", j)
results[ep] = save(ep, "list", data)

print("=== oitm SAP item master — enumerate FG to bust the 200-cap ===")
ep = "/barcode/items/oitm/"
seen = {}
for q in [
    "",
    "?search=FG00001",
    "?search=FG00002",
    "?search=FG00003",
    "?search=FG00004",
]:
    j = get(ep + q)
    rows = (
        j if isinstance(j, list) else j.get("results", j if isinstance(j, list) else [])
    )
    for it in rows or []:
        code = it.get("item_code") or it.get("ItemCode")
        if code:
            seen[code] = it
data = sorted(seen.values(), key=lambda x: x.get("item_code", ""))
results[ep] = save(ep, "list", data)

print("=== SAP-item lookup proxies (search-gated; sampled, redundant w/ oitm) ===")
for ep in ["/quality-control/sap-items/", "/production-execution/sap/items/"]:
    seen = {}
    for q in [
        "?search=FG00001",
        "?search=FG00002",
        "?search=FG00003",
        "?search=FG00004",
        "?search=oil",
    ]:
        try:
            j = get(ep + q)
            rows = j if isinstance(j, list) else j.get("results", [])
            for it in rows or []:
                k = (
                    it.get("item_code")
                    or it.get("ItemCode")
                    or json.dumps(it, sort_keys=True)
                )
                seen[k] = it
        except Exception:
            pass
    data = list(seen.values())
    results[ep] = save(ep, "list", data)

print(
    f"\nDONE. gap endpoints captured: {len(results)}  added/updated records: {sum(results.values())}"
)
