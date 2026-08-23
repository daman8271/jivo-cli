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

The flags themselves live in `acc/apbatch/readback.py`, shared with `acc batch`,
so a gap found once is reported the same way whichever path made the draft.
"""
import argparse, json, os, pathlib, re, subprocess, sys

CLI = None
COMPANY = None
SAP = None


def find_repo():
    here = pathlib.Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / "sap-b1" / "cli" / "sapb1").exists():
            return p
    sys.exit("readback: cannot find jivo-cli/sap-b1/cli/sapb1")


REPO = find_repo()
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

try:
    from acc.apbatch import rules                                       # noqa: E402
    from acc.apbatch import readback as apreadback                      # noqa: E402
    from acc.apbatch.sap import SapCli, SapError                        # noqa: E402
except ImportError as e:                                                # noqa: E402
    print("readback: your checkout is missing acc/apbatch — git pull (or you are on a stale "
          f"copy of jivo-cli). Python said: {e}", file=sys.stderr)
    sys.exit(3)

inr = rules.inr


def load_env(path):
    """--env decides the login; exported values (e.g. the bridge's SAPB1_HOST/PORT) still win."""
    for line in open(path):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


def q(entity, flt=None, select=None):
    """The one door to SAP. Everything below goes through here."""
    try:
        return SAP.query(entity, filter=flt, select=select, company=COMPANY)
    except SapError as e:
        msg = str(e).splitlines()[0]
        if "cannot reach" in msg or "deadline exceeded" in msg:
            raise RuntimeError(f"CANNOT REACH SAP ({msg}) — connection problem, not a data answer; off-office: bash connections/sap-home-bridge.sh then SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000")
        raise RuntimeError(f"{entity}: {msg}")


class _ShimSap:
    """Lets acc.apbatch call back through q(), so one monkeypatch covers everything."""

    def query(self, entity, filter=None, select=None, **kw):
        return q(entity, filter, select)


def main():
    global CLI, COMPANY, SAP
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docentry", type=int, help="Drafts DocEntry returned by sapb1 draft")
    ap.add_argument("--expect-total", type=float, help="grand total printed on the paper")
    ap.add_argument("--expect-qty", type=float, help="total pieces printed on the paper")
    ap.add_argument("--company")
    ap.add_argument("--env", help="per-operator env file next to sapb1")
    a = ap.parse_args()
    repo = REPO
    CLI = repo / "sap-b1" / "cli" / "sapb1"
    COMPANY = a.company
    if a.env:
        env_path = pathlib.Path(a.env) if os.path.isabs(a.env) else CLI.parent / a.env
        if not env_path.exists():
            print(f"readback: --env {a.env}: no such file — looked in {env_path}. Operator env "
                  f"files live next to sapb1 ({CLI.parent}).", file=sys.stderr)
            sys.exit(3)
        load_env(env_path)
    os.environ.setdefault("SAPB1_TIMEOUT", "120")
    SAP = SapCli(repo=repo, company=COMPANY, allow_writes=False)
    shim = _ShimSap()

    d = apreadback.read_draft(shim, a.docentry)
    if not d:
        sys.exit(f"readback: Drafts {a.docentry} not found (exit 3)")
    owner = apreadback.draft_owner(shim, d)
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
    print(f"   taxable {inr(taxable)} · tax {inr(d['VatSum'])} · rounding {d.get('RoundingDiffAmount')} · TDS {inr(d['WTAmount'])} · TOTAL {inr(d['DocTotal'])}")

    bp = q("BusinessPartners", f"CardCode eq '{d['CardCode']}'", "CardCode,SubjectToWithholdingTax,BPWithholdingTaxCollection")
    expect = {}
    if a.expect_qty is not None:
        expect["open_qty"] = a.expect_qty
    if a.expect_total is not None:
        expect["gross"] = a.expect_total
    flags = apreadback.readback_flags(d, expect=expect, bp=bp[0] if bp else None, origin="paper")

    for be in apreadback.base_entries(d):
        g = q("PurchaseDeliveryNotes", f"DocEntry eq {be}", "DocEntry,DocNum,DocumentStatus,DocumentLines")
        if g:
            g = g[0]
            closed = apreadback.base_line_flags(d, g)
            print(f"   base GRPO {g['DocNum']} (DocEntry {be}) {g['DocumentStatus']}" + (f" — lines {sorted({l['BaseLine'] for l in lines if l.get('BaseEntry') == be} & {gl['LineNum'] for gl in g['DocumentLines'] if gl.get('LineStatus') != 'bost_Open'})} already CLOSED" if closed else " — base lines still open ✓"))
            flags.extend(closed)

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
