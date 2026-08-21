#!/usr/bin/env python3
"""precheck — everything SAP needs to know before an A/P invoice draft is made.

Read-only. Runs `sapb1 query` (Service Layer, GET) and prints:
  1. is this vendor invoice already in SAP (posted invoice / open draft)?
  2. vendor card, branch for the buyer GSTIN, TDS setup
  3. the GRPO the invoice must be drawn from (its open lines = the draft lines)
  4. how JIVO booked this vendor's last invoices (series, sub-type, tax, whs, TDS)
  5. the numbering series for the posting month
and writes the proposed draft payload to --out. It never writes to SAP.

Exit codes: 0 ready (payload written) · 2 already exists in SAP · 3 cannot build (ambiguous / missing)

Example:
  precheck.py --ref "26-27/1450" --vendor SSY --gstin 06AACCJ4223F1Z0 \
      --inv-date 2026-08-17 --gate-date 2026-08-18 --qty 5870 \
      --note "GE-2026-9529 | Veh HR69G3463 | e-Way 352314494869" --out /tmp/ap.json
"""
import argparse, collections, datetime as dt, json, os, pathlib, re, subprocess, sys

CLI = None
COMPANY = None
HANA = None


def find_repo():
    here = pathlib.Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / "sap-b1" / "cli" / "sapb1").exists():
            return p
    sys.exit("precheck: cannot find jivo-cli/sap-b1/cli/sapb1 above " + str(here))


def load_env(path):
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()


def q(entity, flt=None, select=None, orderby=None, top=None, all_=False):
    cmd = [str(CLI), "query", entity, "--json"]
    if flt:
        cmd += ["--filter", flt]
    if select:
        cmd += ["--select", select]
    if orderby:
        cmd += ["--orderby", orderby]
    if top:
        cmd += ["--top", str(top)]
    if all_:
        cmd += ["--all"]
    if COMPANY:
        cmd += ["--company", COMPANY]
    r = subprocess.run(cmd, cwd=CLI.parent, capture_output=True, text=True)
    if r.returncode != 0:
        msg = (r.stderr.strip().splitlines() or ["query failed"])[-1]
        raise RuntimeError(f"{entity}: {msg}")
    return json.loads(r.stdout or "[]")


def hana(sql):
    """Optional cross-check via hana-sql (read-only). Returns list of rows (tab-split) or None."""
    if not HANA or not HANA.exists():
        return None
    env = os.environ.get("HANA_ENV") or (HANA.parent.parent / "connections" / "hana.env")
    r = subprocess.run([str(HANA), "-env", str(env), sql], capture_output=True, text=True)
    if r.returncode != 0 or "QUERY ERROR" in r.stdout:
        return None
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    return [l.split("\t") for l in lines[1:]] if len(lines) > 1 else []


def inr(n):
    neg = n < 0
    n = abs(float(n))
    i, f = f"{n:.2f}".split(".")
    last3, rest = i[-3:], i[:-3]
    if rest:
        rest = re.sub(r"\B(?=(\d{2})+(?!\d))", ",", rest) + ","
    return ("-" if neg else "") + "₹" + rest + last3 + "." + f


def fy_indicator(d):
    """SAP period indicator like AUG-26-27 (JIVO financial year April–March)."""
    fy_start = d.year if d.month >= 4 else d.year - 1
    return f"{d.strftime('%b').upper()}-{fy_start % 100:02d}-{(fy_start + 1) % 100:02d}"


def main():
    global CLI, COMPANY, HANA
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", required=True, help="vendor's invoice number exactly as printed (goes to NumAtCard)")
    ap.add_argument("--vendor", required=True, help="part of the vendor name as in SAP (case-insensitive), or a CardCode")
    ap.add_argument("--inv-date", required=True, help="vendor invoice date YYYY-MM-DD (TaxDate)")
    ap.add_argument("--gate-date", help="gate-in date YYYY-MM-DD from JIVO's gate stamp (DocDate). Default: the GRPO's date")
    ap.add_argument("--gstin", help="buyer GSTIN printed on the invoice — selects the branch")
    ap.add_argument("--bpl", type=int, help="branch id if you already know it (overrides --gstin)")
    ap.add_argument("--grpo", type=int, help="GRPO DocNum if written on the paper (e.g. 2026086669)")
    ap.add_argument("--qty", type=float, help="total pieces on the invoice — used to pick the GRPO and to verify")
    ap.add_argument("--total", type=float, help="invoice grand total as printed — verified against the GRPO")
    ap.add_argument("--note", default="", help="extra text for Remarks (gate entry GE-…, vehicle, e-way bill, approvals)")
    ap.add_argument("--company", default=None, help="SAP company DB (default: env/.env, normally JIVO_OIL_HANADB)")
    ap.add_argument("--env", help="per-operator env file next to sapb1 (e.g. navdeep-user36.env) — decides the draft's owner")
    ap.add_argument("--out", help="write the proposed draft payload JSON here")
    a = ap.parse_args()

    repo = find_repo()
    CLI = repo / "sap-b1" / "cli" / "sapb1"
    HANA = repo / "hana-sql" / "hana-sql"
    COMPANY = a.company
    if a.env:
        load_env(a.env if os.path.isabs(a.env) else CLI.parent / a.env)
    problems, warnings = [], []
    print(f"== precheck for vendor ref {a.ref!r} · company {COMPANY or os.environ.get('SAPB1_COMPANYDB') or '(default .env)'} · login {os.environ.get('SAPB1_USER') or '(default .env)'}")

    # 1. already in SAP?
    posted = q("PurchaseInvoices", f"NumAtCard eq '{a.ref}'", "DocEntry,DocNum,CardCode,DocDate,DocTotal,Cancelled")
    drafts = q("Drafts", f"NumAtCard eq '{a.ref}' and DocObjectCode eq 'oPurchaseInvoices'",
               "DocEntry,DocNum,CardCode,DocDate,DocTotal,UserSign,AuthorizationStatus,DocumentStatus")
    open_drafts = [d for d in drafts if d.get("DocumentStatus") == "bost_Open"]
    live = [p for p in posted if p.get("Cancelled") != "tYES"]
    print("\n[1] already in SAP?")
    for p in live:
        print(f"    POSTED A/P invoice DocEntry {p['DocEntry']} DocNum {p['DocNum']} {p['CardCode']} {p['DocDate'][:10]} {inr(p['DocTotal'])}")
    for d in open_drafts:
        print(f"    OPEN DRAFT DocEntry {d['DocEntry']} (doc no {d['DocNum']}) {d['CardCode']} {d['DocDate'][:10]} {inr(d['DocTotal'])} owner user {d['UserSign']} {d['AuthorizationStatus']}")
    if not live and not open_drafts:
        print("    none — nothing posted, no open A/P-invoice draft with this vendor ref")

    # 2. vendor, branch, TDS
    print("\n[2] vendor / branch / TDS")
    v = a.vendor.strip()
    if re.fullmatch(r"[A-Z]+\d{6,}", v.upper()):
        bps = q("BusinessPartners", f"CardCode eq '{v.upper()}'",
                "CardCode,CardName,CardType,SubjectToWithholdingTax,BPWithholdingTaxCollection,PayTermsGrpCode,Valid,Frozen,CurrentAccountBalance")
    else:
        bps = q("BusinessPartners", f"CardType eq 'cSupplier' and contains(CardName,'{v.upper()}')",
                "CardCode,CardName,CardType,SubjectToWithholdingTax,BPWithholdingTaxCollection,PayTermsGrpCode,Valid,Frozen,CurrentAccountBalance")
    if len(bps) != 1:
        for b in bps:
            print(f"    candidate {b['CardCode']} {b['CardName']}")
        problems.append(f"vendor match is not unique ({len(bps)} hits for {v!r}) — pass --vendor <CardCode>")
        bp = None
    else:
        bp = bps[0]
        wt = [w.get("WTCode") for w in bp.get("BPWithholdingTaxCollection") or []]
        print(f"    {bp['CardCode']} {bp['CardName']} · valid {bp['Valid']} frozen {bp['Frozen']} · balance {inr(bp['CurrentAccountBalance'])} ({'JIVO owes them' if bp['CurrentAccountBalance'] < 0 else 'they owe JIVO'})")
        print(f"    TDS: SubjectToWithholdingTax={bp['SubjectToWithholdingTax']} codes={wt or '-'} · payment terms group {bp['PayTermsGrpCode']}")
        if bp["Frozen"] == "tYES" or bp["Valid"] != "tYES":
            problems.append("vendor card is frozen/invalid")

    branches = q("BusinessPlaces", None, "BPLID,BPLName,FederalTaxID,Disabled")
    bpl = None
    if a.bpl:
        bpl = next((b for b in branches if b["BPLID"] == a.bpl), None)
    elif a.gstin:
        bpl = next((b for b in branches if (b.get("FederalTaxID") or "").upper() == a.gstin.upper()), None)
        if not bpl:
            problems.append(f"no branch carries GSTIN {a.gstin} — branches: " + ", ".join(f"{b['BPLID']}={b['BPLName']}:{b.get('FederalTaxID')}" for b in branches))
    else:
        warnings.append("no --gstin/--bpl given: branch taken from the GRPO")
    if bpl:
        print(f"    branch {bpl['BPLID']} {bpl['BPLName']} (GSTIN {bpl['FederalTaxID']}, disabled {bpl['Disabled']})")

    # 3. GRPO
    print("\n[3] GRPO (the invoice is drawn from it — never re-key the lines)")
    grpo = None
    if a.grpo:
        g = q("PurchaseDeliveryNotes", f"DocNum eq {a.grpo}")
        grpo = g[0] if len(g) == 1 else None
        if not grpo:
            problems.append(f"GRPO DocNum {a.grpo} not found")
    if not grpo:
        g = q("PurchaseDeliveryNotes", f"NumAtCard eq '{a.ref}'")
        g = [x for x in g if x.get("Cancelled") != "tYES"]
        if len(g) == 1:
            grpo = g[0]
        elif len(g) > 1:
            problems.append(f"{len(g)} GRPOs carry vendor ref {a.ref}: " + ", ".join(str(x["DocNum"]) for x in g) + " — pass --grpo")
    if not grpo and bp:
        since = (dt.date.fromisoformat(a.inv_date) - dt.timedelta(days=45)).isoformat()
        cands = q("PurchaseDeliveryNotes", f"CardCode eq '{bp['CardCode']}' and DocumentStatus eq 'bost_Open' and DocDate ge '{since}'", orderby="DocEntry desc")
        scored = []
        for c in cands:
            openq = sum(l["RemainingOpenQuantity"] for l in c["DocumentLines"] if l.get("LineStatus") == "bost_Open")
            scored.append((c, openq))
            print(f"    open GRPO {c['DocNum']} (DocEntry {c['DocEntry']}) {c['DocDate'][:10]} ref {c.get('NumAtCard')!r} open qty {openq:g} total {inr(c['DocTotal'])}")
        if a.qty is not None:
            hit = [c for c, openq in scored if abs(openq - a.qty) < 0.001]
            if len(hit) == 1:
                grpo = hit[0]
                warnings.append(f"GRPO chosen by quantity match ({a.qty:g}) — its vendor ref is {grpo.get('NumAtCard')!r}, confirm it is this invoice")
        if not grpo:
            problems.append("no single GRPO identified — pass --grpo <DocNum> (it is usually handwritten on the paper)")
    lines = []
    if grpo:
        lines = [l for l in grpo["DocumentLines"] if l.get("LineStatus") == "bost_Open" and l.get("RemainingOpenQuantity", 0) > 0]
        print(f"    using GRPO {grpo['DocNum']} DocEntry {grpo['DocEntry']} · {grpo['DocDate'][:10]} · status {grpo['DocumentStatus']} · branch {grpo['BPL_IDAssignedToInvoice']} · comments {grpo.get('Comments')!r}")
        for l in lines:
            print(f"      line {l['LineNum']}: {l['ItemCode']} {l['ItemDescription']} · open {l['RemainingOpenQuantity']:g} {l.get('MeasureUnit') or ''} @ {l['UnitPrice']} = {inr(l['LineTotal'])} · {l['TaxCode']} · whs {l['WarehouseCode']} · cc {l.get('CostingCode')} · from PO entry {l.get('BaseEntry')}")
        if not lines:
            problems.append("GRPO has no open lines — it is already invoiced")
        if grpo.get("DocumentStatus") != "bost_Open":
            problems.append("GRPO is closed — already invoiced")
        if bp and grpo["CardCode"] != bp["CardCode"]:
            problems.append(f"GRPO belongs to {grpo['CardCode']}, not {bp['CardCode']}")
        if bpl and grpo["BPL_IDAssignedToInvoice"] != bpl["BPLID"]:
            problems.append(f"GRPO branch {grpo['BPL_IDAssignedToInvoice']} ≠ invoice branch {bpl['BPLID']}")
        if not bpl:
            bpl = next((b for b in branches if b["BPLID"] == grpo["BPL_IDAssignedToInvoice"]), None)
        qsum = sum(l["RemainingOpenQuantity"] for l in lines)
        tsum = sum(l["LineTotal"] for l in lines)
        vsum = sum(l["TaxTotal"] for l in lines)
        print(f"    open qty {qsum:g} · taxable {inr(tsum)} · tax {inr(vsum)} · gross {inr(tsum + vsum)}")
        if a.qty is not None and abs(qsum - a.qty) > 0.001:
            problems.append(f"invoice qty {a.qty:g} ≠ GRPO open qty {qsum:g}")
        if a.total is not None and abs(round(tsum + vsum) - round(a.total)) > 1:
            problems.append(f"invoice total {inr(a.total)} ≠ GRPO gross {inr(tsum + vsum)} (rounding ±1 allowed)")

    # 4. template: last posted invoices for this vendor
    print("\n[4] how JIVO booked this vendor before (last 3 posted A/P invoices)")
    subtype, tmpl = "bod_GSTTaxInvoice", []
    if bp:
        try:
            tmpl = q("PurchaseInvoices", f"CardCode eq '{bp['CardCode']}' and Cancelled eq 'tNO'", orderby="DocEntry desc", top=3)
        except RuntimeError as e:
            warnings.append(f"could not read previous invoices ({e})")
            tmpl = []
        for t in tmpl:
            wtl = {l.get("WTLiable") for l in t["DocumentLines"]}
            print(f"    {t['NumAtCard']} · posting {t['DocDate'][:10]} doc {t['TaxDate'][:10]} due {t['DocDueDate'][:10]} · series {t['Series']} {t['DocumentSubType']} · branch {t['BPL_IDAssignedToInvoice']} · TDS {t['WTAmount']} (lines WTLiable {','.join(sorted(x for x in wtl if x))}) · total {inr(t['DocTotal'])}")
            print(f"        remarks: {t.get('Comments')!r}")
        if tmpl:
            subtype = collections.Counter(t["DocumentSubType"] for t in tmpl).most_common(1)[0][0]
    wt_liable = bool(bp and bp["SubjectToWithholdingTax"] == "boYES")
    wt_rate = None
    if wt_liable:
        codes = [w.get("WTCode") for w in bp.get("BPWithholdingTaxCollection") or []]
        if codes:
            try:
                wc = q("WithholdingTaxCodes", f"WTCode eq '{codes[0]}'")
                if wc:
                    wt_rate = wc[0].get("Rate")
                    print(f"    TDS code {codes[0]} {wc[0].get('WTName') or ''} rate {wt_rate}%")
            except RuntimeError as e:
                warnings.append(f"could not read TDS rate ({e}) — expected TDS not estimated")

    # 5. numbering series for the posting month
    print("\n[5] numbering series for the posting month")
    gate = a.gate_date or (grpo["DocDate"][:10] if grpo else None)
    if not gate:
        problems.append("no gate-in date (--gate-date) and no GRPO to take it from")
    series = None
    if gate and bpl:
        gd = dt.date.fromisoformat(gate)
        month_start = gd.replace(day=1).isoformat()
        same_month = q("PurchaseInvoices", f"DocDate ge '{month_start}' and BPL_IDAssignedToInvoice eq {bpl['BPLID']} and DocumentSubType eq '{subtype}'", "DocEntry,Series", orderby="DocEntry desc", top=20)
        same_month += q("Drafts", f"DocObjectCode eq 'oPurchaseInvoices' and DocDate ge '{month_start}' and BPL_IDAssignedToInvoice eq {bpl['BPLID']} and DocumentSubType eq '{subtype}'", "DocEntry,Series", orderby="DocEntry desc", top=20)
        cnt = collections.Counter(r["Series"] for r in same_month if r.get("Series"))
        if cnt:
            series = cnt.most_common(1)[0][0]
            print(f"    from {sum(cnt.values())} {subtype} docs posted/drafted this month in branch {bpl['BPLID']}: series {dict(cnt)} → using {series}")
        rows = hana(f"SELECT \"Series\",\"SeriesName\",\"DocSubType\" FROM {os.environ.get('SAPB1_COMPANYDB', COMPANY or 'JIVO_OIL_HANADB')}.NNM1 WHERE \"ObjectCode\"='18' AND \"Indicator\"='{fy_indicator(gd)}' AND \"BPLId\"={bpl['BPLID']} AND \"Locked\"='N'")
        if rows is not None:
            print(f"    NNM1 {fy_indicator(gd)} branch {bpl['BPLID']}: " + ", ".join(f"{r[0]}={r[1]}({r[2]})" for r in rows))
            want = {"bod_GSTTaxInvoice": "GA", "bod_None": "--"}.get(subtype)
            ga = [r for r in rows if len(r) > 2 and r[2] == want]
            ga_ids = {int(r[0]) for r in ga}
            if not series:
                if len(ga) == 1:
                    series = int(ga[0][0])
                    print(f"    → series {series} from NNM1 (first document of the month)")
                elif len(ga) > 1:
                    problems.append(f"first {subtype} document of the month and NNM1 has several candidates {sorted(ga_ids)} — pick by hand (the xx_G series is the normal vendor-invoice one; CNxx is not)")
            elif series not in ga_ids:
                warnings.append(f"this month's documents use series {series}, which NNM1 does not list as {want} for branch {bpl['BPLID']} — double-check")
        if not series:
            problems.append("numbering series unknown for this month/branch — look it up (reference/series-and-errors.md) and add \"Series\" by hand")

    # payload
    payload = None
    if grpo and bp and bpl and not problems:
        po_nums = []
        for l in lines:
            if l.get("BaseType") == 22 and l.get("BaseEntry"):
                po = q("PurchaseOrders", f"DocEntry eq {l['BaseEntry']}", "DocNum")
                if po and po[0]["DocNum"] not in po_nums:
                    po_nums.append(po[0]["DocNum"])
        m = re.search(r"GATE ENTRY NO\.?\s*(\d+)", grpo.get("Comments") or "", re.I)
        parts = [f"Based On Goods Receipt PO {grpo['DocNum']}"]
        if po_nums:
            parts.append("PO " + ", ".join(str(p) for p in po_nums))
        if m:
            parts.append(f"GATE ENTRY NO {m.group(1)}")
        if a.note:
            parts.append(a.note.strip())
        comments = " | ".join(parts)[:254]
        payload = {
            "CardCode": bp["CardCode"],
            "DocDate": gate,
            "TaxDate": a.inv_date,
            "NumAtCard": a.ref,
            "BPL_IDAssignedToInvoice": bpl["BPLID"],
            "Series": series,
            "DocumentSubType": subtype,
            "Comments": comments,
            "DocumentLines": [],
        }
        for l in lines:
            row = {
                "BaseType": 20, "BaseEntry": grpo["DocEntry"], "BaseLine": l["LineNum"],
                "ItemCode": l["ItemCode"], "Quantity": l["RemainingOpenQuantity"], "UnitPrice": l["UnitPrice"],
                "TaxCode": l["TaxCode"], "WarehouseCode": l["WarehouseCode"],
            }
            if l.get("CostingCode"):
                row["CostingCode"] = l["CostingCode"]
            if wt_liable:
                row["WTLiable"] = "tYES"
            payload["DocumentLines"].append(row)
        tsum = sum(l["LineTotal"] for l in lines); vsum = sum(l["TaxTotal"] for l in lines)
        tds = round(tsum * (wt_rate or 0) / 100) if wt_liable and wt_rate else 0
        print("\n[6] expected after SAP accepts it")
        print(f"    gross {inr(tsum + vsum)} · TDS {inr(tds)} · payable ≈ {inr(round(tsum + vsum) - tds)} · due date = SAP's terms from doc date")

    print("\n== verdict")
    for w in warnings:
        print(f"    ⚠ {w}")
    if live or open_drafts:
        print("    ✗ ALREADY IN SAP — do not draft again. Compare the existing record to the paper instead.")
        rc = 2
    elif problems:
        for p in problems:
            print(f"    ✗ {p}")
        rc = 3
    else:
        print("    ✓ ready to draft (still: dry-run → show the operator → only then --yes)")
        rc = 0
    if payload and rc == 0 and a.out:
        with open(a.out, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"    payload → {a.out}")
    elif payload and rc == 0:
        print(json.dumps(payload, indent=2))
    sys.exit(rc)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        sys.exit(f"precheck: {e}")
