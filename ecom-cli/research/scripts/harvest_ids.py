#!/usr/bin/env python3
"""Harvest REAL identifier values from live list responses.

Skill rule 1: never send a parameter value you have not observed. A value
read out of a live 200 response IS observed - that is the difference between
this and the factory incident, where invented `?channel=X` values hit a
Django get_or_create and created six production rows.

So: fetch a known-good collection, take an id that already exists, and use
only that. A get_or_create keyed on an existing row returns the existing row
and creates nothing.

READ-ONLY. GET only. Every source path here already returned 200 in run 1.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

SP = os.path.dirname(os.path.abspath(__file__))
BASE = "https://ecom.jivo.in"
TOKEN = json.load(open(os.path.join(SP, "token.json")))["access"]


def get(path):
    req = urllib.request.Request(BASE + path, method="GET", headers={
        "Authorization": f"Bearer {TOKEN}", "Accept": "application/json",
        "User-Agent": "jivo-cli-rescrape/1.0 (read-only endpoint survey)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:400].decode("utf-8", "replace")
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}"


ids = {}
notes = []

# --- platform slugs, from the app's own live data (never from a guess) ---
st, d = get("/api/dashboard/platform-expiry-alerts")
if st == 200:
    slugs = sorted({p["slug"] for p in d.get("platforms", []) if p.get("slug")})
    ids["platform_slug_from_expiry_alerts"] = slugs
    notes.append(f"platform-expiry-alerts reports {len(slugs)} slugs: {slugs}")

st, d = get("/api/platform/ads-summary")
if st == 200 and isinstance(d, dict):
    pf = d.get("platforms") or d.get("rows") or []
    got = sorted({r.get("platform") or r.get("slug") for r in pf
                  if isinstance(r, dict) and (r.get("platform") or r.get("slug"))})
    if got:
        ids["platform_slug_from_ads_summary"] = got

# --- dashboard table names: the keys of table-counts ARE the table ids ---
st, d = get("/api/dashboard/table-counts")
if st == 200 and isinstance(d, dict):
    tables = sorted(k for k, v in d.items() if isinstance(v, int))
    ids["dashboard_table"] = tables
    notes.append(f"table-counts exposes {len(tables)} table names")

# --- chatbot conversation ids ---
st, d = get("/api/chatbot/conversations")
if st == 200:
    rows = d if isinstance(d, list) else d.get("results", [])
    ids["chatbot_conversation_id"] = [r["id"] for r in rows[:3] if "id" in r]

# --- upload ids ---
st, d = get("/api/uploads")
if st == 200:
    rows = d.get("results", []) if isinstance(d, dict) else d
    ids["upload_id"] = [r.get("upload_id") or r.get("id") for r in rows[:3]]

# --- notification ids ---
st, d = get("/api/notifications")
if st == 200:
    rows = d.get("notifications", []) if isinstance(d, dict) else d
    ids["notification_id"] = [r["id"] for r in rows[:3] if "id" in r]

# --- SAP distributor card codes ---
st, d = get("/api/sap/distributors")
if st == 200:
    rows = d.get("data", []) if isinstance(d, dict) else d
    ids["sap_card_code"] = [r["CardCode"] for r in rows[:3] if "CardCode" in r]

# --- SAP sales invoice DocEntry ---
st, d = get("/api/sap/sales-invoices")
if st == 200:
    rows = d.get("data", []) if isinstance(d, dict) else d
    ids["sap_doc_entry"] = [r["DocEntry"] for r in rows[:3] if "DocEntry" in r]

out = {"ids": ids, "notes": notes, "harvested_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
json.dump(out, open(os.path.join(SP, "observed-ids.json"), "w"), indent=1, default=str)
for k, v in ids.items():
    print(f"{k:38} {str(v)[:150]}")
print()
for n in notes:
    print("note:", n)
