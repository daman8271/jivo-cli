"""Original PO line normalizer. No network calls; no customer identifiers escape.

All-month requested and accepted online books are deliberately separate. OMS
scope is checked on both company and item category, never inferred from FG code.
"""
from __future__ import annotations
import collections
import datetime as dt
import hashlib
import json
import math
import re

TERMINAL = {"COMPLETED", "REJECTED", "BILLING_REJECTED", "CANCELLED", "CANCELED", "CLOSED", "FULFILLED"}

def number(value):
    if isinstance(value, bool): return None
    try:
        x = float(value)
        return x if math.isfinite(x) else None
    except (ValueError, TypeError): return None

def positive(value): return max(0.0, number(value) or 0.0)

def date(value):
    if not isinstance(value, str): return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo: parsed = parsed.astimezone(dt.timezone(dt.timedelta(hours=5, minutes=30)))
        return parsed.date().isoformat()
    except ValueError:
        try: return dt.date.fromisoformat(value[:10]).isoformat()
        except ValueError: return None

def opaque(parts):
    return hashlib.sha256(json.dumps(parts, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()[:28]

def bucket(amount, due, today, month, out):
    if not due: out["undatedLitres"] += amount
    else:
        if due < today: out["overdueLitres"] += amount
        if due.startswith(month): out["dueThisMonthLitres"] += amount
        if due[:7] > month: out["laterDueLitres"] += amount
        if due[:7] <= month: out["planningDueLitres"] += amount

def buckets():
    return {k: 0.0 for k in ("dueThisMonthLitres", "overdueLitres", "laterDueLitres", "undatedLitres", "planningDueLitres")}

def identity_name(name):
    # Only formatting and approved 16-to-20 carton transition are normalized; product/oil
    # grade words remain significant. No fuzzy remapping to another SKU.
    s = str(name or "").upper().strip()
    s = re.sub(r"\b(?:JIVO)\b", "", s)
    s = re.sub(r"\b(?:16|20)\s*(?:PCS|PIECES)\b", "20 PCS", s)
    s = re.sub(r"\bKGS\b", "KG", s)
    s = re.sub(r"\b(?:LITRES?|LITERS?|LTRS?)\b", "LTR", s)
    return " ".join(re.findall(r"[A-Z0-9]+", s))

def factory_pack(entry):
    explicit = number(entry.get("packLitres"))
    if explicit is not None: return explicit
    name = str(entry.get("name") or entry.get("ItemName") or "").upper()
    if "COMBO" in name or "+" in name or " SET" in name: return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*(LTRS?|LITRES?|LITERS?|ML[S]?)\b", name)
    return float(match[1]) / (1000 if match[2].startswith("ML") else 1) if match else None

def verify_factory_mapping(code, source_name, source_pack, catalog):
    entry = catalog.get(str(code)) if code else None
    if not entry: return False, "Current factory SKU identity not verified"
    factory_name = entry.get("name") or entry.get("ItemName")
    if not source_name or identity_name(source_name) != identity_name(factory_name): return False, "Original source product name conflicts with current factory SKU identity"
    pack = factory_pack(entry)
    if not pack or number(source_pack) is None or source_pack <= 0 or abs(pack-source_pack) > .001: return False, "Source sales unit conflicts with verified factory piece size; no bundle conversion assumed"
    return True, "Original source product name and numeric unit agree with current factory SKU identity; planner must separately verify BOM identity"

def normalize_sources(amazon, qcomm, products, oms, *, as_of, coverage="partial", coverage_note="", cached_trade=None, factory_identity=None, planner_identity=None):
    """Return {demandBook, orders, items}. Inputs are RAW original row lists.

    coverage describes discovery, not warehouse/fulfilment correctness. Unknown
    unit/mapping rows remain in gross reconciliation; never guessed by name.
    """
    today = date(as_of)
    if today is None: raise ValueError("Valid source timestamp required")
    month = today[:7]
    mapping = collections.defaultdict(set)
    source_names = collections.defaultdict(set)
    factory_identity = factory_identity or {}
    planner_identity = planner_identity or {}
    for r in products:
        if r.get("sku_sap_code"):
            source_names[(str(r.get("format") or "").upper(), str(r.get("format_sku_code") or "").casefold())].add(str(r.get("sku_sap_name") or ""))
            mapping[(str(r.get("format") or "").upper(), str(r.get("format_sku_code") or "").casefold())].add(str(r["sku_sap_code"]))
    online = {**buckets(), "grossOpenLitres": 0.0, "acceptedOpenLitres": 0.0, "acceptedPlanningDueLitres": 0.0,
              "quickCommerceLitres": 0.0, "amazonLitres": 0.0, "amazonAcceptedRemainingLitres": 0.0,
              "unacceptedRequestedLitres": 0.0, "openValueExGst": 0.0, "openPoCount": 0,
              "priorMonthOpenLitres": 0.0, "amazonPriorMonthOpenLitres": 0.0, "priorMonthOpenPoCount": 0,
              "amazonPriorMonthOpenPoCount": 0, "expiredExcludedLitres": 0.0, "unmappedLitres": 0.0,
              "unknownUnitLitres": 0.0, "quantityMismatchLitres": 0.0, "unknownUnitLineCount": 0, "unknownUnitOtherLineCount": 0, "unknownUnitBeverageLineCount": 0, "unknownUnitUnclassifiedLineCount": 0, "mappingConflictLitres": 0.0, "mappingConflictAcceptedLitres": 0.0,
              "outsideOilScopePlanningDueLitres": 0.0, "outsideOilScopeAcceptedPlanningDueLitres": 0.0, "outsideOilScopeLitres": 0.0, "outsideOilScopeAcceptedLitres": 0.0,
              "byPlatform": [], "dateBasis": "Delivery date, otherwise PO expiry; Amazon uses expiry. Missing delivery/expiry stays undated. Calendar-month due and overdue overlap. planningDueLitres includes all overdue plus current-month dates exactly once."}
    platforms = collections.defaultdict(lambda: {"litres": 0.0, "acceptedLitres": 0.0, "pos": set()})
    allpos, priorpos, amzpriorpos = set(), set(), set()
    orders, items, notes = [], {}, []
    identities = collections.Counter()
    for source, rows in (("amazon", amazon), ("qcomm", qcomm)):
        for r in rows:
            platform = "AMAZON" if source == "amazon" else str(r.get("format") or "UNKNOWN").upper()
            expiry = date(r.get("expiry_date") if source == "amazon" else r.get("po_expiry_date"))
            created = date(r.get("order_date") if source == "amazon" else r.get("po_date"))
            delivery = date(r.get("delivery_date")) if source == "qcomm" else None
            due = delivery or expiry
            gross = max(0, positive(r.get("total_order_liters")) - positive(r.get("total_delivered_liters")))
            if expiry and expiry < today:
                online["expiredExcludedLitres"] += gross
                continue
            state = str(r.get("po_status") if source == "amazon" else r.get("open_close") or "").upper()
            if state in TERMINAL: continue
            accepted = max(0, positive(r.get("total_accepted_liters")) - positive(r.get("total_delivered_liters"))) if source == "amazon" else gross
            # Do not expand an accepted commitment beyond the requested residual.
            accepted = min(gross, accepted)
            po = opaque([source, platform, r.get("po_number")])
            allpos.add(po)
            platforms[platform]["pos"].add(po)
            platforms[platform]["litres"] += gross
            platforms[platform]["acceptedLitres"] += accepted
            online["grossOpenLitres"] += gross
            online["acceptedOpenLitres"] += accepted
            online["amazonLitres" if source == "amazon" else "quickCommerceLitres"] += gross
            if source == "amazon": online["amazonAcceptedRemainingLitres"] += accepted
            if created and created < month + "-01":
                online["priorMonthOpenLitres"] += gross; priorpos.add(po)
                if source == "amazon": online["amazonPriorMonthOpenLitres"] += gross; amzpriorpos.add(po)
            if due and due[:7] <= month: online["acceptedPlanningDueLitres"] += accepted
            bucket(gross, due, today, month, online)
            amount_field = "total_deliver_amt_exclusive" if source == "amazon" else "total_delivered_amt_exclusive"
            online["openValueExGst"] += max(0, positive(r.get("total_order_amt_exclusive")) - positive(r.get(amount_field)))
            candidates = mapping[(platform, str(r.get("sku_code") or "").casefold())]
            code = str(r["sap_sku_code"]) if source == "amazon" and r.get("sap_sku_code") else next(iter(candidates)) if len(candidates) == 1 else None
            names = source_names[(platform, str(r.get("sku_code") or "").casefold())]
            source_name = str(r.get("sap_sku_name") or (next(iter(names)) if len(names)==1 else "") or r.get("sku_name") or "")
            if not code: online["unmappedLitres"] += gross
            pack = number(r.get("per_liter"))
            # Raw numeric per_liter is the source unit conversion. per_ltr_unit is TEXT.
            requested_pieces = max(0, positive(r.get("requested_qty")) - positive(r.get("received_qty"))) if source == "amazon" else max(0, positive(r.get("order_qty")) - positive(r.get("delivered_qty")))
            pieces = max(0, positive(r.get("accepted_qty")) - positive(r.get("received_qty"))) if source == "amazon" else requested_pieces
            if not pack or pack <= 0:
                online["unknownUnitLitres"] += gross; online["unknownUnitLineCount"] += int(requested_pieces > 0)
                family = str(r.get("category_head") or "").upper()
                key = "unknownUnitOtherLineCount" if family == "OTHER" else "unknownUnitBeverageLineCount" if family in ("BEVERAGE","BEVERAGES") else "unknownUnitUnclassifiedLineCount"
                online[key] += int(requested_pieces > 0)
                continue
            if abs(requested_pieces * pack - gross) > .11 or abs(pieces * pack - accepted) > .11:
                online["quantityMismatchLitres"] += gross
                continue
            if str(r.get("category_head") or "").upper() in ("BEVERAGE", "BEVERAGES", "OTHER"):
                online["outsideOilScopeLitres"] += gross
                online["outsideOilScopeAcceptedLitres"] += accepted
                if due and due[:7] <= month:
                    online["outsideOilScopePlanningDueLitres"] += gross
                    online["outsideOilScopeAcceptedPlanningDueLitres"] += accepted
                continue
            if accepted <= 0: continue
            verified, reason = verify_factory_mapping(code, source_name, pack, factory_identity)
            if verified:
                verified, planner_reason = verify_factory_mapping(code, source_name, pack, planner_identity)
                if not verified: reason = "Planner/BOM identity unresolved: " + planner_reason
            if not verified:
                online["mappingConflictLitres"] += gross
                online["mappingConflictAcceptedLitres"] += accepted
            signature = [source, platform, r.get("po_number"), r.get("sku_code"), r.get("external_id"), r.get("fulfillment_center") or r.get("location"), created, expiry, due, requested_pieces, pieces]
            key = opaque(signature); occurrence = identities[key]; identities[key] += 1
            line_id = opaque([key, occurrence])
            if code:
                name = r.get("sap_sku_name") or r.get("sku_name") or code
                items[code] = {"name": str(name)[:240], "uom": "PCS"}
            orders.append({"docnum": "ECOM-" + po, "sourceLineId": line_id, "date": created or today, "due": due or "", "expiresAt": expiry, "dueBasis": "delivery" if delivery else "expiry" if expiry else "undated",
                "code": code, "code_mapping_verified": verified, "mappingStatus": "verified" if verified else "unverified", "mappingReason": reason, "mappingIssue": None if verified else reason, "sourceSkuCode": code, "sourceProductName": source_name, "sourcePackLitres": pack, "pieces": pieces, "packLitres": pack, "remainingLitres": accepted,
                "requestedPieces": requested_pieces, "requestedLitres": gross, "channel": platform, "_src": "ECOM-EXACT",
                "platform": platform, "remainingBasis": "accepted-minus-received" if source == "amazon" else "ordered-minus-delivered", "companyScope": "ecom platform original SKU mapping; no company inferred from code", "status": "OPEN", "is_exact_sku_due": True,
                "demand_basis": ("Original Amazon PO line; accepted minus received. Requested residual remains separately in gross open book. " if source == "amazon" else "Original open master_po line; ordered minus delivered. ") + ("Due from delivery_date." if delivery else "Due proxy from expiry_date." if expiry else "No delivery/expiry date: held as undated."),
                "value_basis": "No per-line realised price implied; gross source value reported separately."})
    online["openPoCount"] = len(allpos)
    online["priorMonthOpenPoCount"] = len(priorpos)
    online["amazonPriorMonthOpenPoCount"] = len(amzpriorpos)
    online["unacceptedRequestedLitres"] = online["grossOpenLitres"] - online["acceptedOpenLitres"]
    online["byPlatform"] = [{"platform": p, "litres": v["litres"], "acceptedLitres": v["acceptedLitres"], "poCount": len(v["pos"])} for p,v in sorted(platforms.items())]
    trade = {**buckets(), "grossOpenLitres": 0.0, "openOrderCount": 0, "openValueExGst": None,
             "companyScope": "OMS header company=1 AND line category=OIL. No trade channel classification inferred.", "scopeVerified": True,
             "otherCompanyOpenLitres": 0.0, "otherCategoryOpenLitres": 0.0, "unknownCompanyOpenLitres": 0.0,
             "sourceOrderCount": len(oms), "statusCounts": {}, "isNetOutstanding": False}
    tradepos = set(); statuses = collections.Counter()
    for r in oms:
        if r.get("id") is None: raise ValueError("OMS order identity missing")
        status = str(r.get("status") or "UNKNOWN").upper(); statuses[status] += 1
        if status in TERMINAL: continue
        company = str(r.get("company") or ""); created = date(r.get("created_at")); due = date(r.get("delivery_date"))
        po = opaque(["OMS", r.get("id")]); included = False
        for index, row in enumerate(r.get("items") or []):
            qty, lit = positive(row.get("qty")), positive(row.get("ltrs"))
            category = str(row.get("category") or "").upper()
            if company != "1":
                trade["otherCompanyOpenLitres" if company else "unknownCompanyOpenLitres"] += lit
                if not company: trade["scopeVerified"] = False
                continue
            if category != "OIL": trade["otherCategoryOpenLitres"] += lit; continue
            included = True; trade["grossOpenLitres"] += lit; bucket(lit, due, today, month, trade)
            code = str(row["item_code"]) if row.get("item_code") else None
            if code: items[code] = {"name": str(row.get("item_name") or code)[:240], "uom": "PCS"}
            pack = lit / qty if qty > 0 and lit > 0 else None
            source_name = str(row.get("item_name") or "")
            verified, reason = verify_factory_mapping(code, source_name, pack, factory_identity)
            if verified:
                verified, planner_reason = verify_factory_mapping(code, source_name, pack, planner_identity)
                if not verified: reason = "Planner/BOM identity unresolved: " + planner_reason
            scheme = positive(row.get("qty_scheme"))
            if scheme: notes.append("OMS free scheme pieces exist; line ltrs may not include them. Keep scheme demand separate until reconciled.")
            item_identity = row.get("id") if row.get("id") is not None else index
            orders.append({"docnum": "OMS-" + po, "sourceLineId": opaque(["OMS",r.get("id"),item_identity]), "date": created or today, "due": due or "", "expiresAt": None,
                "code": code, "code_mapping_verified": verified, "mappingStatus": "verified" if verified else "unverified", "mappingReason": reason, "mappingIssue": None if verified else reason, "sourceSkuCode": code, "sourceProductName": source_name, "sourcePackLitres": pack, "pieces": qty, "schemePieces": scheme, "packLitres": pack, "remainingLitres": lit, "requestedLitres": lit,
                "channel": "OIL", "_src": "OMS", "dueBasis": "delivery" if due else "undated", "remainingBasis": "full-ordered-quantity-on-nonterminal-order", "companyScope": "company=1; category=OIL", "status": status, "is_exact_sku_due": bool(due),
                "demand_basis": "Fresh original nonterminal order line. Source exposes full qty/ltrs, no delivered quantity; not proved net outstanding.",
                "value_basis": "Header/item amount tax basis not attested; no ex-GST value asserted."})
        if included: tradepos.add(po)
    trade["openOrderCount"] = len(tradepos); trade["statusCounts"] = dict(statuses)
    if cached_trade: trade["previousCachedBook"] = cached_trade
    notes.extend([coverage_note, "Online gross is requested/ordered minus delivered, all creation months, expired dates excluded. Accepted Amazon residual is the conservative scheduling basis; unaccepted requested litres remain visible separately.",
        "Prior-month online is all platforms; amazonPriorMonthOpenLitres reproduces Mark3's specifically Amazon-only previous-month badge.",
        "Due-this-month is calendar month; overdue overlaps it. planningDueLitres is the non-overlapping actionable total due by month end. Later-month orders remain in gross book.",
        "Expiry/delivery dates are source fields, not a new promise. No aggregate platform-to-SKU allocation is performed.",
        "Online all-platform gross includes source-classified non-Oil items; BEVERAGE/OTHER litres are visible as outsideOilScopeLitres and never scheduled on Oil machines.",
        "Unknown-unit lines are counted separately: explicit OTHER/BEVERAGE are not Oil litre demand; unclassified unknown units remain an unresolved coverage gap, not zero litres.",
        "Ecom codes are source namespace references until current factory name and unit identity agree; conflicts retain original gross litres and cannot schedule wrong-oil or wrong-pack production.",
        "OMS full quantity on nonterminal orders is not a delivered-net balance; accepted open statuses are provisional. Company and line category are independently checked."])
    if online["unknownUnitUnclassifiedLineCount"]: coverage = "partial"
    return {"asOf": as_of, "demandBook": {"asOf": as_of, "coverage": coverage, "online": online, "trade": trade, "reconciliationNotes": list(dict.fromkeys(x for x in notes if x))}, "orders": orders, "items": items}

def normalize_directory(directory, *, as_of=None):
    from pathlib import Path
    d = Path(directory)
    status = json.loads((d / "oms-discovery-status.json").read_text())
    source_reads = json.loads((d / "read-status.json").read_text()) if (d / "read-status.json").exists() else {}
    # Slow complete discovery must not make earlier PO reads look newly fetched.
    stamp = as_of or min(x for x in (status["started"], source_reads.get("asOf")) if x)
    details = [json.loads(p.read_text())["results"] for p in d.glob("oms-[0-9]*.json")]
    headers = json.loads((d / "oms-header-snapshot.json").read_text()) if (d / "oms-header-snapshot.json").exists() else {}
    if headers.get("complete"):
        stamp = as_of or min(x for x in (headers["asOf"], source_reads.get("asOf")) if x)
    failed_ids = set(headers.get("activeDetailErrors", []))
    details = [x for x in details if str(x["id"]) not in failed_ids]
    by_id = {str(x["id"]):x for x in details}
    unknown = []
    for identifier, h in headers.get("orders", {}).items():
        if identifier in by_id:
            by_id[identifier]["status"] = h["status"]
        elif h["status"] not in TERMINAL:
            unknown.append({"id": opaque(["OMS",identifier]), "status": h["status"], "createdAt": date(h.get("created_at")), "companyScope":"unknown", "litres":None})
    raw = lambda name: json.loads((d / (name + "-rows.json")).read_text())
    old = json.loads((d / "state-snapshot.json").read_text()) if (d / "state-snapshot.json").exists() else {}
    cached = old.get("oms", {}).get("open_total") or {}
    prior = {"litres": cached.get("litres"), "count": cached.get("count"), "asOf": old.get("collected_at"), "basis": "Prior Mark3 nonterminal status cache, includes other companies and stale statuses; comparison only."}
    note = f"OMS original detail IDs 1–{status['through']} enumerated; {status['counts'].get('ok',0)} found, {status['counts'].get('missing',0)} absent, {status['counts'].get('error',0)} errors. Discovery started {status['started']}. Last numeric frontier contains absent IDs; this is source-readable OMS coverage, not a realised delivery ledger."
    identifiers = status.get("ids", {})
    trailing_absent = all(identifiers.get(str(i), identifiers.get(i)) == "missing" for i in range(status["through"] - 11, status["through"] + 1))
    complete = bool(headers.get("complete") or status.get("complete")) and trailing_absent and not unknown
    factory = json.loads((d / "factory-identity.json").read_text()) if (d / "factory-identity.json").exists() else {}
    planner = json.loads((d / "planner-identity.json").read_text()).get("items", {}) if (d / "planner-identity.json").exists() else {}
    factory_items = factory.get("items", {})
    catalog_clock = factory.get("asOf")
    if factory.get("ok") is False or not factory.get("coverage", {}).get("completeWithinRange") or not catalog_clock or abs((dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")) - dt.datetime.fromisoformat(catalog_clock.replace("Z", "+00:00"))).total_seconds()) > 86400:
        factory_items = {}
    conflicts = []
    for code, item in factory_items.items():
        if code not in planner: continue
        fn = item.get("name") or item.get("ItemName") or ""
        pn = planner[code].get("name") or ""
        fp = factory_pack(item)
        item["packLitres"] = fp
        pp = number(planner[code].get("packLitres"))
        if identity_name(fn) != identity_name(pn) or (pp and fp and abs(pp-fp)>.001):
            conflicts.append({"code":code,"reason":"Current factory identity conflicts with inherited planner/BOM identity", "factoryName":fn,"plannerName":pn,"factoryPackLitres":fp,"plannerPackLitres":pp})
    result = normalize_sources(raw("amazon"), raw("qcomm"), raw("products"), details, as_of=stamp, coverage="complete" if complete else "partial", coverage_note=note, cached_trade=prior, factory_identity=factory_items, planner_identity=planner)
    result["factoryIdentity"] = {"asOf":catalog_clock,"items":{code:{"name":item.get("name") or item.get("ItemName"),"packLitres":item.get("packLitres"),"uom":item.get("uom")} for code,item in factory_items.items()}}
    result["identityConflicts"] = conflicts
    result["demandBook"]["online"]["sourceAsOf"] = source_reads.get("asOf")
    result["demandBook"]["trade"]["sourceAsOf"] = headers.get("asOf") if headers.get("complete") else status["started"]
    result["demandBook"]["trade"]["discoveryCompletedAt"] = status["checkedAt"]
    result["demandBook"]["trade"]["unknownActiveOrderCount"] = len(unknown)
    result["demandBook"]["trade"]["unknownActiveOrders"] = unknown
    result["demandBook"]["trade"]["isComplete"] = complete and not unknown
    if unknown:
        result["demandBook"]["coverage"] = "partial"
        result["demandBook"]["trade"]["scopeVerified"] = False
        result["demandBook"]["reconciliationNotes"].append(f"{len(unknown)} fresh active OMS headers cannot supply company/items/litres because their detail serializer fails. Trade litres/count above are the verified Oil subtotal, not a complete company balance. Unknowns are not zero.")
    if headers.get("asOf"):
        result["demandBook"]["trade"]["headerCoverage"] = {k:headers.get(k) for k in ("userCount", "headerCount", "activeCount", "highestHeaderId", "frontierThrough", "frontierAbsentTail", "complete")}
        result["demandBook"]["trade"]["headerAsOf"] = headers["asOf"]
    return result

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(); p.add_argument("--raw-dir", required=True); p.add_argument("--out", required=True); a = p.parse_args()
    from pathlib import Path
    result = normalize_directory(a.raw_dir)
    Path(a.out).write_text(json.dumps({"asOf":result["asOf"],"ok":result["demandBook"]["coverage"]=="complete","data":result},indent=2))
