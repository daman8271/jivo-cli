#!/usr/bin/env python3
"""readback — read a draft back from SAP and say what is wrong with it, if anything.

Read-only. Use straight after `sapb1 draft purchase-invoice … --yes` with the DocEntry SAP returned.

  readback.py 54938 --expect-total 208388 --expect-qty 5870

Prints the draft as SAP holds it, then flags:
  · TDS came out 0 although the vendor is TDS-liable (happens on API-made drafts)
  · total / quantity differ from the paper
  · base GRPO lines no longer open (someone else invoiced them)
  · owner + the exact place to open it in the SAP client
Exit 0 clean · 1 flags raised · 3 not found
"""
import argparse, json, os, pathlib, re, subprocess, sys

CLI = None
COMPANY = None


def find_repo():
    here = pathlib.Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / "sap-b1" / "cli" / "sapb1").exists():
            return p
    sys.exit("readback: cannot find jivo-cli/sap-b1/cli/sapb1")


def load_env(path):
    """--env decides the login; exported values (e.g. the bridge's SAPB1_HOST/PORT) still win."""
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def q(entity, flt=None, select=None):
    cmd = [str(CLI), "query", entity, "--json"]
    if flt:
        cmd += ["--filter", flt]
    if select:
        cmd += ["--select", select]
    if COMPANY:
        cmd += ["--company", COMPANY]
    r = subprocess.run(cmd, cwd=CLI.parent, capture_output=True, text=True)
    if r.returncode != 0:
        msg = (r.stderr.strip().splitlines() or ["query failed"])[-1]
        if "cannot reach" in msg or "deadline exceeded" in msg:
            raise RuntimeError(f"CANNOT REACH SAP ({msg}) — connection problem, not a data answer; off-office: bash connections/sap-home-bridge.sh then SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000")
        raise RuntimeError(f"{entity}: {msg}")
    return json.loads(r.stdout or "[]")


def inr(n):
    neg = n < 0
    n = abs(float(n))
    i, f = f"{n:.2f}".split(".")
    last3, rest = i[-3:], i[:-3]
    if rest:
        rest = re.sub(r"\B(?=(\d{2})+(?!\d))", ",", rest) + ","
    return ("-" if neg else "") + "₹" + rest + last3 + "." + f


def main():
    global CLI, COMPANY
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docentry", type=int, help="Drafts DocEntry returned by sapb1 draft")
    ap.add_argument("--expect-total", type=float, help="grand total printed on the paper")
    ap.add_argument("--expect-qty", type=float, help="total pieces printed on the paper")
    ap.add_argument("--company")
    ap.add_argument("--env", help="per-operator env file next to sapb1")
    a = ap.parse_args()
    repo = find_repo()
    CLI = repo / "sap-b1" / "cli" / "sapb1"
    COMPANY = a.company
    if a.env:
        load_env(a.env if os.path.isabs(a.env) else CLI.parent / a.env)
    os.environ.setdefault("SAPB1_TIMEOUT", "120")

    rows = q("Drafts", f"DocEntry eq {a.docentry}")
    if not rows:
        sys.exit(f"readback: Drafts {a.docentry} not found (exit 3)")
    d = rows[0]
    flags = []
    owner = q("Users", f"InternalKey eq {d['UserSign']}", "UserCode,UserName")
    owner = f"{owner[0]['UserCode']} ({owner[0]['UserName']})" if owner else f"user {d['UserSign']}"
    lines = d["DocumentLines"]
    qty = sum(l["Quantity"] for l in lines)
    taxable = sum(l["LineTotal"] for l in lines)

    print(f"== Draft {d['DocEntry']} · {d['DocObjectCode']} · doc no {d['DocNum']} · {d['DocumentStatus']} · approval {d['AuthorizationStatus']} · owner {owner}")
    print(f"   {d['CardCode']} {d['CardName']} · vendor ref {d['NumAtCard']}")
    print(f"   posting {d['DocDate'][:10]} · doc {d['TaxDate'][:10]} · due {d['DocDueDate'][:10]} · branch {d.get('BPLName')} ({d['BPL_IDAssignedToInvoice']}) · series {d['Series']} {d['DocumentSubType']}")
    print(f"   remarks: {d.get('Comments')!r}")
    for l in lines:
        base = f"{ {20: 'GRPO', 22: 'PO'}.get(l.get('BaseType'), l.get('BaseType')) } {l.get('BaseEntry')}/{l.get('BaseLine')}" if l.get("BaseEntry") else "NOT based on any document"
        print(f"   line {l['LineNum']}: {l['ItemCode']} {l['ItemDescription']} · {l['Quantity']:g} {l.get('MeasureUnit') or ''} @ {l['UnitPrice']} = {inr(l['LineTotal'])} · {l['TaxCode']} {inr(l['TaxTotal'])} · whs {l['WarehouseCode']} · WTLiable {l.get('WTLiable')} · {base}")
        if not l.get("BaseEntry"):
            flags.append(f"line {l['LineNum']} is not drawn from a GRPO — adding it would receive stock a second time")
    print(f"   taxable {inr(taxable)} · tax {inr(d['VatSum'])} · rounding {d.get('RoundingDiffAmount')} · TDS {inr(d['WTAmount'])} · TOTAL {inr(d['DocTotal'])}")

    bp = q("BusinessPartners", f"CardCode eq '{d['CardCode']}'", "CardCode,SubjectToWithholdingTax,BPWithholdingTaxCollection")
    if bp and bp[0]["SubjectToWithholdingTax"] == "boYES" and not d["WTAmount"]:
        codes = [w.get("WTCode") for w in bp[0].get("BPWithholdingTaxCollection") or []]
        flags.append(f"TDS is 0 but the vendor is TDS-liable (codes {codes}) — tick WTax Liable on every row in the SAP client before Add")
    if a.expect_qty is not None and abs(qty - a.expect_qty) > 0.001:
        flags.append(f"quantity {qty:g} ≠ paper {a.expect_qty:g}")
    if a.expect_total is not None:
        gross = d["DocTotal"] + d["WTAmount"]
        if abs(round(gross) - round(a.expect_total)) > 1:
            flags.append(f"gross {inr(gross)} (total + TDS) ≠ paper {inr(a.expect_total)}")
    for be in sorted({l["BaseEntry"] for l in lines if l.get("BaseType") == 20 and l.get("BaseEntry")}):
        g = q("PurchaseDeliveryNotes", f"DocEntry eq {be}", "DocEntry,DocNum,DocumentStatus,DocumentLines")
        if g:
            g = g[0]
            used = {l["BaseLine"] for l in lines if l.get("BaseEntry") == be}
            closed = [gl["LineNum"] for gl in g["DocumentLines"] if gl["LineNum"] in used and gl.get("LineStatus") != "bost_Open"]
            print(f"   base GRPO {g['DocNum']} (DocEntry {be}) {g['DocumentStatus']}" + (f" — lines {closed} already CLOSED" if closed else " — base lines still open ✓"))
            if closed:
                flags.append(f"GRPO {g['DocNum']} lines {closed} were invoiced by someone else — this draft will fail on Add")

    print("\n   see it in SAP B1: Purchasing – A/P → Purchasing Reports → Document Drafts Report → tick A/P Invoice + Open Only, User = "
          f"{owner.split(' ')[0]} (or All) → row {d['CardName']} · {d['NumAtCard']} · {inr(d['DocTotal'])}")
    print("   nothing posts until a person opens it and presses Add (it will then go to the approval queue).")
    if flags:
        print("\n== flags")
        for f in flags:
            print(f"   ⚠ {f}")
        sys.exit(1)
    print("\n== clean: matches expectations")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        sys.exit(f"readback: {e}")
