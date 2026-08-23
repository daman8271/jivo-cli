#!/usr/bin/env python3
"""precheck — everything SAP needs to know before an A/P invoice draft is made.

Read-only. Runs `sapb1 query` (Service Layer, GET) and prints:
  1. is this vendor invoice already in SAP (posted invoice / open draft — by vendor ref AND by GRPO)?
  2. vendor card, branch for the buyer GSTIN, TDS setup
  3. the GRPO the invoice must be drawn from (its open lines = the draft lines)
  4. how JIVO booked this vendor's last invoices (series, sub-type, tax, whs, TDS)
  5. the numbering series for the posting month
and writes the proposed draft payload to --out. It never writes to SAP.

Exit codes: 0 ready (payload written) · 2 already exists in SAP · 3 cannot build (ambiguous / missing) · 4 cannot reach SAP

Precedence for connection settings: exported environment (e.g. the bridge's
SAPB1_HOST/PORT) > --env file > sap-b1/cli/.env. So `--env navdeep-user36.env`
changes the login, not the route.

The decisions live in `acc/apbatch` (rules.py, context.py) and are shared with
`acc batch`, which does the same job 50 rows at a time. This file is the paper's
side of it: the argparse, the paper-vs-GRPO comparisons, the narrative and the
exit contract above. Change a rule in apbatch and both paths change together.

Example:
  precheck.py --ref "26-27/1450" --vendor SSY --gstin 06AACCJ4223F1Z0 \
      --inv-date 2026-08-17 --gate-date 2026-08-18 --qty 5870 --total 208388 --po 220626014 \
      --item "Carton Jivo 1 Ltr x 20 pcs 40 gm" \
      --note "GE-2026-9529 | Veh HR69G3463 | e-Way 352314494869" --out /tmp/ap-draft.json
"""
import argparse, collections, datetime as dt, json, os, pathlib, re, subprocess, sys

CLI = None
COMPANY = None
HANA = None
SAP = None
COMPANIES = ["JIVO_OIL_HANADB", "JIVO_MART_HANADB", "JIVO_BEVERAGES_HANADB"]


class Unreachable(RuntimeError):
    pass


def find_repo():
    here = pathlib.Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / "sap-b1" / "cli" / "sapb1").exists():
            return p
    sys.exit("precheck: cannot find jivo-cli/sap-b1/cli/sapb1 above " + str(here))


REPO = find_repo()
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

try:
    from acc.apbatch import rules                                    # noqa: E402
    from acc.apbatch.context import HanaSql                          # noqa: E402
    from acc.apbatch.sap import (SapCli, SapError, SapUnreachable,   # noqa: E402
                                 odata_str, read_env_file)
except ImportError as e:                                             # noqa: E402
    # The decisions moved into acc/apbatch on 2026-08-24. A checkout without it
    # is a stale copy (a Drive zip, or a pull that has not happened), and the
    # skill would otherwise die with a bare ModuleNotFoundError that reads like
    # a Python problem instead of a sync problem.
    print("precheck: your checkout is missing acc/apbatch — git pull (or you are on a stale "
          f"copy of jivo-cli). Python said: {e}", file=sys.stderr)
    sys.exit(3)

# Kept as module-level names because this script's own output format depends on
# them and the characterization test monkeypatches q().
inr = rules.inr
fy_indicator = rules.fy_indicator
tokens = rules.tokens


def q(entity, flt=None, select=None, orderby=None, top=None, company=None):
    """The one door to SAP. Everything below goes through here."""
    try:
        return SAP.query(entity, filter=flt, select=select, orderby=orderby, top=top,
                         company=company or COMPANY)
    except SapUnreachable as e:
        raise Unreachable(str(e).splitlines()[0])
    except SapError as e:
        raise RuntimeError(f"{entity}: {e}")


def hana(sql):
    """Optional cross-check via hana-sql (read-only). Returns rows (tab-split) or None."""
    return HANA.rows(sql) if HANA else None


def main():
    global CLI, COMPANY, HANA, SAP
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", required=True, help="vendor's invoice number exactly as printed (goes to NumAtCard)")
    ap.add_argument("--vendor", required=True, help="part of the vendor name as in SAP (case-insensitive), or a CardCode")
    ap.add_argument("--inv-date", required=True, help="vendor invoice date YYYY-MM-DD (TaxDate)")
    ap.add_argument("--gate-date", help="gate-in date YYYY-MM-DD from JIVO's gate stamp (DocDate). Default: the GRPO's date")
    ap.add_argument("--gstin", help="buyer GSTIN printed on the invoice — selects the branch (several branches can share one; the GRPO's branch wins)")
    ap.add_argument("--bpl", type=int, help="branch id if you already know it (overrides --gstin)")
    ap.add_argument("--grpo", type=int, help="GRPO DocNum if written on the paper (e.g. 2026086669)")
    ap.add_argument("--po", help="buyer's order no(s) printed on the paper, comma-separated — checked against the GRPO's base POs")
    ap.add_argument("--qty", type=float, help="total pieces on the invoice — used to pick the GRPO and to verify")
    ap.add_argument("--total", type=float, help="invoice grand total as printed — verified against the GRPO")
    ap.add_argument("--item", help="item description as printed on the paper — compared with the GRPO line's SAP item name")
    ap.add_argument("--note", default="", help="extra text for Remarks (gate entry GE-…, vehicle, e-way bill, approvals)")
    ap.add_argument("--company", default=None, help="SAP company DB: JIVO_OIL_HANADB = Jivo Wellness Pvt Ltd (default), JIVO_MART_HANADB, JIVO_BEVERAGES_HANADB = '(Beverage Unit) Jivo Wellness'")
    ap.add_argument("--env", help="per-operator env file next to sapb1 (e.g. navdeep-user36.env) — decides the draft's owner; does not override exported SAPB1_HOST/PORT")
    ap.add_argument("--out", help="write the proposed draft payload JSON here (use a plain filename — vendor refs contain '/')")
    a = ap.parse_args()

    repo = REPO
    CLI = repo / "sap-b1" / "cli" / "sapb1"
    HANA = HanaSql(repo)
    COMPANY = a.company
    if a.env:
        env_path = pathlib.Path(a.env) if os.path.isabs(a.env) else CLI.parent / a.env
        if not env_path.exists():
            # Carrying on with the default login would put the draft under
            # somebody else's name — the one thing --env decides.
            print(f"precheck: --env {a.env}: no such file — looked in {env_path}. Operator env "
                  f"files live next to sapb1 ({CLI.parent}).", file=sys.stderr)
            sys.exit(3)
        for k, v in read_env_file(env_path).items():
            os.environ.setdefault(k, v)          # exported values (bridge host/port) win
    os.environ.setdefault("SAPB1_TIMEOUT", "120")  # bridged calls are slower than the 30 s default
    SAP = SapCli(repo=repo, company=COMPANY, allow_writes=False)
    dotenv = read_env_file(CLI.parent / ".env")
    company_eff = COMPANY or os.environ.get("SAPB1_COMPANYDB") or dotenv.get("SAPB1_COMPANYDB") or "JIVO_OIL_HANADB"
    user_eff = os.environ.get("SAPB1_USER") or dotenv.get("SAPB1_USER") or "?"
    host_eff = os.environ.get("SAPB1_HOST") or dotenv.get("SAPB1_HOST") or "?"
    problems, warnings = [], []
    print(f"== precheck for vendor ref {a.ref!r} · company {company_eff} · login {user_eff} (the draft's owner) · host {host_eff}")
    if company_eff == "JIVO_OIL_HANADB":
        print("   (JIVO_OIL_HANADB = JIVO WELLNESS PVT LTD. Mart and the Beverage Unit are separate books with the same vendors and GSTINs — pass --company if the paper is theirs.)")

    # 1. already in SAP? (by vendor ref; the GRPO-keyed check follows in [3])
    ref_lit = odata_str(a.ref)
    posted = q("PurchaseInvoices", f"NumAtCard eq {ref_lit}", "DocEntry,DocNum,CardCode,DocDate,DocTotal,Cancelled")
    drafts = q("Drafts", f"NumAtCard eq {ref_lit} and DocObjectCode eq 'oPurchaseInvoices'",
               "DocEntry,DocNum,CardCode,DocDate,DocTotal,UserSign,AuthorizationStatus,DocumentStatus")
    open_drafts = [d for d in drafts if d.get("DocumentStatus") == "bost_Open"]
    live = [p for p in posted if p.get("Cancelled") != "tYES"]
    print("\n[1] already in SAP? (vendor ref)")
    for p in live:
        print(f"    POSTED A/P invoice DocEntry {p['DocEntry']} DocNum {p['DocNum']} {p['CardCode']} {p['DocDate'][:10]} {inr(p['DocTotal'])}")
    for d in open_drafts:
        print(f"    OPEN DRAFT DocEntry {d['DocEntry']} (doc no {d['DocNum']}) {d['CardCode']} {d['DocDate'][:10]} {inr(d['DocTotal'])} owner user {d['UserSign']} {d['AuthorizationStatus']}")
    if not live and not open_drafts:
        print("    none by vendor ref")

    # 2. vendor, branch, TDS
    print("\n[2] vendor / branch / TDS")
    v = a.vendor.strip()
    sel = "CardCode,CardName,CardType,SubjectToWithholdingTax,BPWithholdingTaxCollection,PayTermsGrpCode,Valid,Frozen,CurrentAccountBalance"
    if re.fullmatch(r"[A-Z]+\d{6,}", v.upper()):
        bps = q("BusinessPartners", f"CardCode eq '{v.upper()}'", sel)
    else:
        bps = q("BusinessPartners", f"CardType eq 'cSupplier' and contains(CardName,'{v.upper()}')", sel)
    bp = None
    if len(bps) != 1:
        for b in bps:
            print(f"    candidate {b['CardCode']} {b['CardName']}")
        problems.append(f"vendor match is not unique ({len(bps)} hits for {v!r}) — pass --vendor <CardCode>")
    else:
        bp = bps[0]
        wt = [w.get("WTCode") for w in bp.get("BPWithholdingTaxCollection") or []]
        print(f"    {bp['CardCode']} {bp['CardName']} · valid {bp['Valid']} frozen {bp['Frozen']} · balance {inr(bp['CurrentAccountBalance'])} ({'JIVO owes them' if bp['CurrentAccountBalance'] < 0 else 'they owe JIVO'})")
        print(f"    TDS: SubjectToWithholdingTax={bp['SubjectToWithholdingTax']} codes={wt or '-'} · payment terms group {bp['PayTermsGrpCode']}")
        if bp["Frozen"] == "tYES" or bp["Valid"] != "tYES":
            problems.append("vendor card is frozen/invalid")

    branches = q("BusinessPlaces", None, "BPLID,BPLName,FederalTaxID,Disabled")
    by_id = {b["BPLID"]: b for b in branches}
    bpl, bpl_matches = None, []
    if a.bpl:
        bpl = by_id.get(a.bpl)
        if not bpl:
            problems.append(f"branch {a.bpl} does not exist")
    elif a.gstin:
        bpl_matches = [b for b in branches if (b.get("FederalTaxID") or "").upper() == a.gstin.upper() and b.get("Disabled") != "tYES"]
        if not bpl_matches:
            problems.append(f"no branch carries GSTIN {a.gstin} — branches: " + ", ".join(f"{b['BPLID']}={b['BPLName']}:{b.get('FederalTaxID')}" for b in branches))
        elif len(bpl_matches) == 1:
            bpl = bpl_matches[0]
        else:
            print(f"    GSTIN {a.gstin} is on {len(bpl_matches)} branches: " + ", ".join(f"{b['BPLID']} {b['BPLName']}" for b in bpl_matches) + " — the GRPO's branch decides")
    else:
        warnings.append("no --gstin/--bpl given: branch taken from the GRPO")
    if bpl:
        print(f"    branch {bpl['BPLID']} {bpl['BPLName']} (GSTIN {bpl['FederalTaxID']})")

    # 3. GRPO
    print("\n[3] GRPO (the invoice is drawn from it — never re-key the lines)")
    grpo = None
    if a.grpo:
        g = q("PurchaseDeliveryNotes", f"DocNum eq {a.grpo}")
        grpo = g[0] if len(g) == 1 else None
        if not grpo:
            problems.append(f"GRPO DocNum {a.grpo} not found")
    if not grpo:
        g = [x for x in q("PurchaseDeliveryNotes", f"NumAtCard eq {ref_lit}") if x.get("Cancelled") == "tNO"]
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
        # is it in another company's books?
        elsewhere = []
        for c in COMPANIES:
            if c == company_eff:
                continue
            try:
                hits = [x for x in q("PurchaseDeliveryNotes", f"NumAtCard eq {ref_lit}", "DocEntry,DocNum,CardCode,DocDate,DocTotal,DocumentStatus", company=c) if x.get("DocumentStatus") == "bost_Open"]
            except RuntimeError:
                hits = []
            for h in hits:
                elsewhere.append(f"{c}: GRPO {h['DocNum']} {h['CardCode']} {h['DocDate'][:10]} {inr(h['DocTotal'])}")
        if elsewhere:
            problems.append("the GRPO for this vendor ref is in ANOTHER company's books — re-run with --company: " + "; ".join(elsewhere))
        else:
            problems.append("no single GRPO identified in any company — pass --grpo <DocNum> (it is usually handwritten on the paper)")

    lines, po_nums = [], []
    if grpo:
        # allow_service=False: a service GRPO reports "no open lines" here, as it
        # always has. That draft shape is `acc batch`'s to prove, not this one's.
        lines = rules.open_lines(grpo, allow_service=False)
        print(f"    using GRPO {grpo['DocNum']} DocEntry {grpo['DocEntry']} · {grpo['DocDate'][:10]} · status {grpo['DocumentStatus']} · branch {grpo['BPL_IDAssignedToInvoice']} · comments {grpo.get('Comments')!r}")
        for l in lines:
            print(f"      line {l['LineNum']}: {l['ItemCode']} {l['ItemDescription']} · open {l['RemainingOpenQuantity']:g} {l.get('MeasureUnit') or ''} @ {l['UnitPrice']} = {inr(l['LineTotal'])} · {l['TaxCode']} · whs {l['WarehouseCode']} · cc {l.get('CostingCode')} · from PO entry {l.get('BaseEntry')}")
            if l.get("BaseType") == 22 and l.get("BaseEntry"):
                po = q("PurchaseOrders", f"DocEntry eq {l['BaseEntry']}", "DocNum")
                if po and po[0]["DocNum"] not in po_nums:
                    po_nums.append(po[0]["DocNum"])
        if po_nums:
            print(f"    base POs: {', '.join(str(p) for p in po_nums)}")
        if a.po:
            paper = [p.strip() for p in a.po.split(",") if p.strip()]
            missing = [p for p in paper if p not in {str(n) for n in po_nums}]
            extra = [str(n) for n in po_nums if str(n) not in paper]
            if missing:
                problems.append(f"paper cites PO {missing} but the GRPO draws from {po_nums} — wrong GRPO, or wrong PO on the paper")
            elif extra:
                warnings.append(f"GRPO also draws from PO {extra}, which the paper does not cite (merged POs — normal, mention it)")
        if a.item and lines:
            names = {l["ItemDescription"] for l in lines}
            pt = tokens(a.item)
            for n in names:
                overlap = len(pt & tokens(n)) / max(1, len(pt))
                print(f"    item name — paper: {a.item!r} · SAP: {n!r} · overlap {overlap:.0%}")
                if overlap < 0.5:
                    warnings.append(f"paper item {a.item!r} vs SAP item {n!r} — same part under JIVO's code? (qty/rate/money decide; say it to the operator)")
        if not lines:
            problems.append("GRPO has no open lines — it is already invoiced")
        if grpo.get("DocumentStatus") != "bost_Open":
            problems.append("GRPO is closed — already invoiced")
        if bp and grpo["CardCode"] != bp["CardCode"]:
            problems.append(f"GRPO belongs to {grpo['CardCode']}, not {bp['CardCode']}")
        g_bpl = by_id.get(grpo["BPL_IDAssignedToInvoice"])
        if bpl and g_bpl and g_bpl["BPLID"] != bpl["BPLID"]:
            problems.append(f"GRPO branch {g_bpl['BPLID']} {g_bpl['BPLName']} ≠ invoice branch {bpl['BPLID']} {bpl['BPLName']}")
        if not bpl and g_bpl:
            if bpl_matches and g_bpl["BPLID"] not in {b["BPLID"] for b in bpl_matches}:
                problems.append(f"GRPO branch {g_bpl['BPLID']} {g_bpl['BPLName']} does not carry GSTIN {a.gstin}")
            else:
                bpl = g_bpl
                print(f"    branch {bpl['BPLID']} {bpl['BPLName']} (from the GRPO, GSTIN {bpl.get('FederalTaxID')})")
        totals = rules.gross_of(lines)
        qsum, tsum, vsum = totals.open_qty, totals.taxable, totals.tax
        print(f"    open qty {qsum:g} · taxable {inr(tsum)} · tax {inr(vsum)} · gross {inr(tsum + vsum)}")
        if a.qty is not None and abs(qsum - a.qty) > 0.001:
            problems.append(f"invoice qty {a.qty:g} ≠ GRPO open qty {qsum:g}")
        if a.total is not None and abs(round(tsum + vsum) - round(a.total)) > 1:
            problems.append(f"invoice total {inr(a.total)} ≠ GRPO gross {inr(tsum + vsum)} (rounding ±1 allowed)")

        # already in SAP, keyed by GRPO (catches drafts with a typo'd/blank vendor ref)
        try:
            cand = q("Drafts", f"DocObjectCode eq 'oPurchaseInvoices' and CardCode eq '{grpo['CardCode']}' and DocumentStatus eq 'bost_Open'", orderby="DocEntry desc")
            seen = {d["DocEntry"] for d in open_drafts}
            for c in cand:
                if c["DocEntry"] in seen:
                    continue
                if rules.draft_targets_grpo(c, grpo["DocEntry"]):
                    print(f"    OPEN DRAFT on this GRPO under a different vendor ref: DocEntry {c['DocEntry']} ref {c.get('NumAtCard')!r} {inr(c['DocTotal'])} owner user {c['UserSign']}")
                    open_drafts.append(c)
        except RuntimeError as e:
            warnings.append(f"could not scan the vendor's open drafts by GRPO ({e})")
    elif not bpl and len(bpl_matches) > 1:
        problems.append("GSTIN matches several branches and there is no GRPO to decide — pass --bpl")

    # 4. template: last posted invoices for this vendor
    print("\n[4] how JIVO booked this vendor before (last 3 posted A/P invoices)")
    subtype, tmpl = "bod_GSTTaxInvoice", []
    if bp:
        try:
            tmpl = q("PurchaseInvoices", f"CardCode eq '{bp['CardCode']}' and Cancelled eq 'tNO'", orderby="DocEntry desc", top=3)
        except RuntimeError as e:
            warnings.append(f"could not read previous invoices ({e})")
        for t in tmpl:
            wtl = {l.get("WTLiable") for l in t["DocumentLines"]}
            print(f"    {t['NumAtCard']} · posting {t['DocDate'][:10]} doc {t['TaxDate'][:10]} due {t['DocDueDate'][:10]} · series {t['Series']} {t['DocumentSubType']} · branch {t['BPL_IDAssignedToInvoice']} · TDS {t['WTAmount']} (lines WTLiable {','.join(sorted(x for x in wtl if x))}) · total {inr(t['DocTotal'])}")
            print(f"        remarks: {t.get('Comments')!r}")
        if tmpl:
            subtype = collections.Counter(t["DocumentSubType"] for t in tmpl).most_common(1)[0][0]
    # The batch decides TDS from precedent (rules.tds_proposal); here the operator
    # is looking at the vendor's last three invoices printed above and decides for
    # themselves, which is what SKILL.md tells them to do.
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
        # Month-BOUNDED, both ends: without the upper bound a July posting checked
        # in August votes on August's documents and takes August's series.
        m0, m1 = rules.month_bounds(gd)
        window = f"DocDate ge '{m0}' and DocDate lt '{m1}'"
        same_month = q("PurchaseInvoices", f"{window} and BPL_IDAssignedToInvoice eq {bpl['BPLID']} and DocumentSubType eq '{subtype}'", "DocEntry,Series", orderby="DocEntry desc", top=20)
        same_month += q("Drafts", f"DocObjectCode eq 'oPurchaseInvoices' and {window} and BPL_IDAssignedToInvoice eq {bpl['BPLID']} and DocumentSubType eq '{subtype}'", "DocEntry,Series", orderby="DocEntry desc", top=20)
        rows = hana(f"SELECT \"Series\",\"SeriesName\",\"DocSubType\" FROM {company_eff}.NNM1 WHERE \"ObjectCode\"='18' AND \"Indicator\"='{fy_indicator(gd)}' AND \"BPLId\"={bpl['BPLID']} AND \"Locked\"='N'")
        choice = rules.pick_series(same_month, rows, subtype, bpl=bpl["BPLID"], docdate=gd)
        cnt = choice.counts
        if cnt:
            series = choice.series
            print(f"    from {sum(cnt.values())} {subtype} docs posted/drafted this month in branch {bpl['BPLID']}: series {cnt} → using {series}")
        if rows is not None:
            print(f"    NNM1 {fy_indicator(gd)} branch {bpl['BPLID']}: " + ", ".join(f"{r[0]}={r[1]}({r[2]})" for r in rows))
            if not cnt and choice.series:
                series = choice.series
                print(f"    → series {series} from NNM1 ({choice.source})")
            if choice.problem:
                problems.append(choice.problem)
            if choice.warning:
                warnings.append(choice.warning)
        if not series:
            problems.append("numbering series unknown for this month/branch — look it up (reference/series-and-errors.md) and add \"Series\" by hand")

    # payload
    payload = None
    if grpo and bp and bpl and not problems:
        base = rules.comments_base(grpo, po_nums)
        draft = rules.build_payload(grpo, lines, bpl["BPLID"], series, subtype)
        # --gate-date, when the operator passes one, overrides the GRPO's date:
        # the stamp on the paper is the posting date (C-0017), and occasionally
        # the GRPO was keyed a day off it.
        draft["DocDate"] = gate
        payload = rules.finalize_payload(draft, num_at_card=a.ref, tax_date=a.inv_date,
                                         wtliable="tYES" if wt_liable else None,
                                         comments=rules.build_comments(base, note=a.note))
        totals = rules.gross_of(lines)
        tsum, vsum = totals.taxable, totals.tax
        tds = round(tsum * (wt_rate or 0) / 100) if wt_liable and wt_rate else 0
        print("\n[6] expected after SAP accepts it")
        print(f"    gross {inr(tsum + vsum)} · TDS {inr(tds)} · payable ≈ {inr(round(tsum + vsum) - tds)} · due date = SAP's terms from doc date")

    print("\n== verdict")
    for w in warnings:
        print(f"    ⚠ {w}")
    if live or open_drafts:
        print("    ✗ ALREADY IN SAP — do not draft again. Compare each record to the paper:")
        for d in open_drafts:
            extra = (f" --expect-total {a.total:g}" if a.total is not None else "") + (f" --expect-qty {a.qty:g}" if a.qty is not None else "")
            print(f"      python3 {pathlib.Path(__file__).with_name('readback.py')} {d['DocEntry']}{extra}")
        if len(open_drafts) > 1:
            print(f"      {len(open_drafts)} open drafts on one invoice — a human must remove the extras in the SAP client (the CLI cannot).")
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
    except Unreachable as e:
        print(f"\nprecheck: CANNOT REACH SAP — this is a connection problem, not a data answer.\n  {e}\n"
              "  From outside the office IP: bash connections/sap-home-bridge.sh, then export SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000 "
              "(and HANA_ENV=connections/hana-office-bridge.env) and re-run.", file=sys.stderr)
        sys.exit(4)
    except RuntimeError as e:
        sys.exit(f"precheck: {e}")
