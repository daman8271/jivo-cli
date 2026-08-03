#!/usr/bin/env python3
"""Hand-authored corrections that outrank every automated overlay.

Each entry states the evidence in place. These exist because an automated
overlay was wrong in a way no amount of cross-lens agreement would have
caught - only a live call settled it.

Writes study-overlay.json, which emit_spec.py applies last.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# The server's REAL allowlist for the {table} parameter: the integer-valued
# keys of a live GET /api/dashboard/table-counts. Lens C derived a different
# list from the SPA source; five of its members are rejected by the server
# (`consolidated_fsn_report`, `meta_data`, `flipkart_state_sales`,
# `total_po_gr`, `SecMaster` all -> {"error":"Table not allowed"}), and it
# also carried the client-side typo `zeptSec`, which the server likewise
# rejects while accepting `zeptoSec` (51,458 rows). A live 200 outranks
# anything read from code.
TABLES = json.load(open(os.path.join(HERE, "observed-tables.json")))

TABLE_DESC = ("Reporting-schema table name, case-sensitive. The valid set is the "
              "key list of `dashboard table-counts`, which is the server's own "
              "allowlist - anything else returns 400 \"Table not allowed\".")

OVERLAY = {}


def put(path, description=None, params=None, drop_params=None):
    e = OVERLAY.setdefault(path, {})
    if description:
        e["description"] = description
    if params:
        e.setdefault("params", []).extend(params)
    if drop_params:
        e["drop_params"] = list(drop_params)


TABLE_PARAM = {"name": "table", "type": "string", "required": True,
               "description": TABLE_DESC, "enum": TABLES}

# ---- the {table} family -----------------------------------------------------
# `expiry-alerts/{…}` takes a TABLE name, not a platform slug. The shipped spec
# calls it `platform`, which is wrong: useDashboardData-<hash>.js maps the SAME
# table-name list through getTableCount() and getExpiryAlerts() and then filters
# the results on `alert.table`. Confirmed live - /expiry-alerts/amazon_inventory
# returns 200, while /expiry-alerts/amazon returns 200 with an empty alerts list,
# i.e. a false empty that reads as "no alerts" when it means "not a table".
put("/api/dashboard/expiry-alerts/{}",
    description=("Expiry alerts for one reporting table. NOTE: the path segment is a "
                 "TABLE name (see `tables counts`), not a platform slug - passing a "
                 "platform returns 200 with an empty list, which is a false negative."),
    params=[TABLE_PARAM], drop_params=["platform"])

for p in ("/api/dashboard/table-columns/{}", "/api/dashboard/table-count/{}",
          "/api/dashboard/table-data/{}", "/api/dashboard/table-distinct/{}/{}"):
    put(p, params=[TABLE_PARAM])

# ---- descriptions the shipped spec got wrong --------------------------------
# The shipped description reads "Platform metadata (slugs, labels, config)".
# The live payload is the Meta (Facebook/Instagram) ads dashboard: 83 campaigns
# with campaign_name / reach / impressions / link_clicks / cpc / cpm / amount_spent.
# The SPA chunk that consumes it is MetaDashboard-<hash>.js. Command name is a
# public contract and does not change; the description must.
put("/api/platform/meta",
    description=("Meta (Facebook/Instagram) advertising dashboard - campaign-level "
                 "reach, impressions, link clicks, CPC, CPM and amount spent. This is "
                 "NOT platform metadata; there is no endpoint that returns the "
                 "platform slug list (use `account me`, field `platforms`)."))

put("/api/reports/raw",
    description=("Raw rows for one report view. `view` is required - a bare call "
                 "returns 400 \"Unknown report view\". The `platform` filter on this "
                 "endpoint takes UPPERCASE display names with spaces (BIG BASKET, "
                 "FLIPKART GROCERY, CITY MALL), NOT the lowercase slugs every other "
                 "endpoint uses."))
put("/api/reports/columns",
    description=("Column definitions for one report view. `view` is required - a bare "
                 "call returns 400 \"Unknown report view\"."))

# ---- SAP: which company this mirror actually serves --------------------------
# Verified against HANA row counts: items 1,349 = Mart OITM (Oil 2,270, Bev 2,192);
# distributors 1,247 = Mart OCRD CardType='S'; sales-invoices 25,157 = Mart OINV;
# inventory-overview 47,908 = Mart OITW. An Accounts operator reading these as
# group or Oil figures will be wrong.
SAP_MART = " Company scope: JIVO MART (JIVO_MART_HANADB), not Oil and not group-wide."
for p, extra in {
    "/api/sap/items": SAP_MART,
    "/api/sap/distributors": (" Despite the name this is the VENDOR master "
                              "(OCRD CardType='S') - ad agencies and suppliers, not "
                              "sales distributors. For distributors use "
                              "`sap platform-distributors`." + SAP_MART),
    "/api/sap/sales-invoices": (" Invoice HEADERS only, and the set includes "
                                "cancelled documents. DocTotal is GST-inclusive. There "
                                "is no credit-note endpoint here, so JIVO turnover "
                                "(invoices net of GST minus credit notes, excluding "
                                "cancelled) is NOT computable from this domain - use "
                                "SAP directly." + SAP_MART),
    "/api/sap/inventory-overview": SAP_MART,
    "/api/sap/stock-by-warehouse": SAP_MART,
    "/api/sap/inventory-finished-goods": SAP_MART,
    "/api/sap/sales-analysis": (" With source=oil this defaults to cardname "
                                "'JIVO MART PVT LTD', i.e. it measures Oil->Mart "
                                "INTERCOMPANY transfers, which JIVO excludes from "
                                "sales (correction C-0005)."),
}.items():
    OVERLAY.setdefault(p, {})["append_description"] = extra

# ---- corrections from the adversarial verification pass ---------------------
# The sap study read only ONE call site for sales-analysis and missed nine
# parameters that two other chunks send. `item_head` is the one that matters:
# JIVO correction C-0003 says to segment the range on U_TYPE
# (PREMIUM/COMMODITY/OTHERS) and never by item-name matching - and without this
# param the CLI leaves an operator no way to do that but name-matching.
put("/api/sap/sales-analysis", params=[
    {"name": "item_head", "type": "string", "required": False,
     "description": ("Segment filter (PREMIUM / COMMODITY / OTHERS). Use this rather "
                     "than matching on item names - JIVO correction C-0003. Valid "
                     "values come back in the response's `filters` block.")},
    {"name": "aggregate", "type": "string", "required": False, "enum": ["item_head"],
     "description": ("Ask the SERVER to aggregate. With aggregate=item_head and "
                     "page_size=1 the response carries a computed `aggregate[]` block, "
                     "so headline totals need no paging.")},
    {"name": "search", "type": "string", "required": False, "description": "Free-text search"},
    {"name": "state", "type": "string", "required": False, "description": "State filter; values come back in the response `filters` block"},
    {"name": "type", "type": "string", "required": False, "description": "Type filter; values come back in the response `filters` block"},
    {"name": "brand", "type": "string", "required": False, "description": "Brand filter; values come back in the response `filters` block"},
    {"name": "sales_person", "type": "string", "required": False, "description": "Salesperson filter; values come back in the response `filters` block"},
    {"name": "nocache", "type": "integer", "required": False, "description": "Set to 1 to bypass the server-side cache"},
    {"name": "fresh", "type": "integer", "required": False, "description": "Set to 1 to force a fresh read"},
])

# The enum was sitting in the very chunk the study cited.
put("/api/sap/inventory-overview", params=[
    {"name": "status", "type": "string", "required": False,
     "enum": ["", "Y", "N"],
     "description": ("Item status: empty = all, Y = active, N = frozen. The dashboard "
                     "sends Y; a bare CLI call therefore returns MORE rows than the UI "
                     "shows - it includes frozen items.")},
])

# Lens C published `status ∈ {shipped, short, not_loaded}` for the shipment
# record endpoint. Those are CLIENT-side line filters read off the browser query
# string, not wire values. The wire values are the shipment lifecycle states.
put("/api/shipment/record", params=[
    {"name": "status", "type": "string", "required": False,
     "enum": ["draft", "pending_approval", "approved", "dispatched"],
     "description": ("Shipment lifecycle state. NOTE: shipped / short / not_loaded are "
                     "client-side row filters in the UI, not values this parameter "
                     "accepts. Unverified - this endpoint is behind the Shipment "
                     "Planner permission gate.")},
])

if __name__ == "__main__":
    json.dump(OVERLAY, open(os.path.join(HERE, "study-overlay.json"), "w"), indent=1)
    print(f"{len(OVERLAY)} correction entries -> study-overlay.json")
    for k, v in sorted(OVERLAY.items()):
        bits = []
        if v.get("description"):
            bits.append("description")
        if v.get("append_description"):
            bits.append("append")
        if v.get("params"):
            bits.append(f"{len(v['params'])} params")
        if v.get("drop_params"):
            bits.append(f"drop {v['drop_params']}")
        print(f"  {k:46} {', '.join(bits)}")
