#!/usr/bin/env python3
"""Follow-up probe: platform-scoped routes against their OWN platform.

Run 2 probed every /api/platform/{slug}/... route with slug=amazon and got 17
x 400. Those 400s were not failures - each body names the platforms the route
IS for, verbatim:

    ["Blinkit Ads Dashboard is available only for Blinkit."]
    ["Monthly landing rate is only available for blinkit, zepto, swiggy,
      bigbasket, flipkart_grocery."]

So every value used here was observed - in a live 400 body from this run, or
in a live 200 payload. Nothing is invented and nothing is enumerated blind.

READ-ONLY, GET only.
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

# route suffix -> platform slugs the server itself named as valid
MATCHED = {
    "bigbasket-ads-daily-dashboard": ["bigbasket"],
    "bigbasket-ads-dashboard": ["bigbasket"],
    "blinkit-ads-dashboard": ["blinkit"],
    "blinkit-brandfund-dashboard": ["blinkit"],
    "blinkit-summary-report": ["blinkit"],
    "flipkart-ads-dashboard": ["flipkart"],
    "flipkart-fsn-dashboard": ["flipkart"],
    "swiggy-ads-daily-dashboard": ["swiggy"],
    "swiggy-ads-dashboard": ["swiggy"],
    "swiggy-brandfund-dashboard": ["swiggy"],
    "zepto-ads-daily-dashboard": ["zepto"],
    "zepto-ads-dashboard": ["zepto"],
    "zepto-brandfund-dashboard": ["zepto"],
    "landing-rate": ["blinkit", "zepto", "swiggy", "bigbasket", "flipkart_grocery"],
    "landing-rate/skus": ["blinkit"],
    "monthly-sales-explorer": ["bigbasket", "blinkit", "swiggy", "zepto"],
    "pendency-dashboard": ["blinkit", "zepto", "swiggy", "bigbasket"],
}

# the two Django-level 404s, retested across several observed slugs: a routing
# 404 is slug-independent, a view-level 404 is not, and the difference decides
# whether the endpoint is dead or merely unavailable for that platform.
RETEST_404 = ["month-on-month-sale", "region-doh-dashboard"]
RETEST_SLUGS = ["blinkit", "zepto", "swiggy", "bigbasket", "flipkart_grocery", "zomato"]


def get(path):
    req = urllib.request.Request(BASE + path, method="GET", headers={
        "Authorization": f"Bearer {TOKEN}", "Accept": "application/json",
        "User-Agent": "jivo-cli-rescrape/1.0 (read-only endpoint survey)"})
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
        body = e.read()[:400].decode("utf-8", "replace")
        rec["error"] = re.sub(r"\s+", " ", body).strip()[:220]
    except Exception as e:
        rec["http"] = 0
        rec["error"] = f"{type(e).__name__}: {e}"
    return rec


results = []
print("== platform-scoped routes against their own platform ==")
for suffix, slugs in MATCHED.items():
    for slug in slugs[:2]:                    # first two is enough to prove routing
        r = get(f"/api/platform/{slug}/{suffix}")
        r["template"] = f"/api/platform/{{}}/{suffix}"
        r["slug"] = slug
        results.append(r)
        print(f'  {r["http"]:>3} /api/platform/{slug}/{suffix}   {r.get("error","")[:90]}')
        time.sleep(0.15)

print("\n== the two 404s, retested across slugs ==")
for suffix in RETEST_404:
    codes = []
    for slug in RETEST_SLUGS:
        r = get(f"/api/platform/{slug}/{suffix}")
        r["template"] = f"/api/platform/{{}}/{suffix}"
        r["slug"] = slug
        results.append(r)
        codes.append(f"{slug}={r['http']}")
        time.sleep(0.12)
    print(f"  {suffix}: {' '.join(codes)}")

print("\n== the 500, retested on other observed DocEntries ==")
obs = json.load(open(os.path.join(SP, "observed-ids.json")))["ids"]
for de in obs.get("sap_doc_entry", [])[:3]:
    r = get(f"/api/sap/sales-invoice-lines/{de}")
    r["template"] = "/api/sap/sales-invoice-lines/{}"
    results.append(r)
    print(f'  {r["http"]:>3} DocEntry={de}  {r.get("error","")[:140]}')
    time.sleep(0.15)

out = sys.argv[1]
with open(out + ".jsonl", "w") as f:
    for r in results:
        f.write(json.dumps(r) + "\n")
from collections import Counter
print("\n== status distribution ==", Counter(r["http"] for r in results))
