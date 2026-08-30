#!/usr/bin/env python3
"""
JIVO Oil — daily production requirement.

    Production Requirement = OIH + MSL − FG in godown − production already released
                             (floored at zero)

Settled definitions (operator, 2026-08-11):
  OIH   Order in hand. OMS pushes an order to SAP only once its approval workflow
        completes, so SAP's OPEN sales orders ARE the approved orders. Verified:
        orders sitting in OMS status Approved/Billing carry no sap_doc_number;
        Completed ones do.
  MSL   35% of the previous CALENDAR month's sales. Net-of-returns vs gross is
        still open — both are computed; NET is used by default.
        Oil→Mart intercompany DOES count as sold.
  FG    Finished goods in BH-BT + BH-PF only.
          BH-BS and BH-PM are the PACKAGING MATERIAL godowns — never finished goods.
          Every other warehouse (BH-SC, GP-FG, PB-JP, BH-FG, BH-GR ...) is out of scope.
  WIP   Production orders already open in SAP are subtracted. A 60-day age cut-off
        applies because SAP carries stale open orders — FG0000030 alone has two
        that have sat at 0% since 2024-11 and 2025-06.
  Units Everything computes in PCS (single bottles — correction C-0001). OMS boxes
        convert on the way in. Litres come from the plan's PER LTRS, falling back to
        the BOM's own oil quantity ÷ BOM yield.

Read-only. Touches nothing.

    python3 jolly/engine/requirement.py [--month YYYY-MM] [--csv out.csv]
"""
import argparse, csv, json, os, subprocess, sys, tempfile
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HANA = os.path.join(REPO, "hana-sql", "hana-sql")
CO = "JIVO_OIL_HANADB"
FG_WAREHOUSES = ("BH-BT", "BH-PF")
MSL_PCT = 0.35
WIP_MAX_AGE_DAYS = 60

SQL = """
SELECT I."ItemCode", I."ItemName", I."U_TYPE", I."U_Sub_Group",
  IFNULL(O."OIH",0) AS OIH, IFNULL(S."SOLD_GROSS",0) AS SOLD_GROSS,
  IFNULL(R."RETURNED",0) AS RETURNED, IFNULL(F."FG_ONHAND",0) AS FG_ONHAND,
  IFNULL(W."OPEN_PROD",0) AS OPEN_PROD, IFNULL(B."LTR_PER_PC",0) AS LTR_PER_PC
FROM {co}.OITM I
LEFT JOIN (SELECT L."ItemCode", SUM(L."OpenQty") AS OIH
  FROM {co}.RDR1 L JOIN {co}.ORDR H ON H."DocEntry"=L."DocEntry"
  WHERE H."DocStatus"='O' AND H."CANCELED"='N' GROUP BY L."ItemCode") O ON O."ItemCode"=I."ItemCode"
LEFT JOIN (SELECT L."ItemCode", SUM(L."Quantity") AS SOLD_GROSS
  FROM {co}.INV1 L JOIN {co}.OINV H ON H."DocEntry"=L."DocEntry"
  WHERE H."DocDate">='{m0}' AND H."DocDate"<'{m1}' AND H."CANCELED"='N'
  GROUP BY L."ItemCode") S ON S."ItemCode"=I."ItemCode"
LEFT JOIN (SELECT L."ItemCode", SUM(L."Quantity") AS RETURNED
  FROM {co}.RIN1 L JOIN {co}.ORIN H ON H."DocEntry"=L."DocEntry"
  WHERE H."DocDate">='{m0}' AND H."DocDate"<'{m1}' AND H."CANCELED"='N'
  GROUP BY L."ItemCode") R ON R."ItemCode"=I."ItemCode"
LEFT JOIN (SELECT "ItemCode", SUM("OnHand") AS FG_ONHAND FROM {co}.OITW
  WHERE "WhsCode" IN ({whs}) GROUP BY "ItemCode") F ON F."ItemCode"=I."ItemCode"
LEFT JOIN (SELECT "ItemCode", SUM("PlannedQty"-"CmpltQty") AS OPEN_PROD FROM {co}.OWOR
  WHERE "Status" IN ('P','R') AND "PostDate">='{wip}' GROUP BY "ItemCode") W ON W."ItemCode"=I."ItemCode"
LEFT JOIN (SELECT C."Father", SUM(C."Quantity")/MAX(T."Qauntity") AS LTR_PER_PC
  FROM {co}.ITT1 C JOIN {co}.OITT T ON T."Code"=C."Father"
  WHERE C."Code" LIKE 'RM%' AND T."TreeType"='P' GROUP BY C."Father") B ON B."Father"=I."ItemCode"
WHERE I."ItemCode" LIKE 'FG%'
  AND (O."OIH">0 OR S."SOLD_GROSS">0 OR F."FG_ONHAND">0)
ORDER BY I."ItemCode"
"""


def prev_month_bounds(today):
    m1 = today.replace(day=1)
    m0 = (m1.replace(day=1) - date.resolution).replace(day=1)
    return m0.isoformat(), m1.isoformat()


def run_sql(sql, env_file=None):
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as fh:
        fh.write(sql)
        path = fh.name
    cmd = [HANA]
    if env_file:
        cmd += ["-env", env_file]
    cmd += ["-csv", "-f", path]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    finally:
        os.unlink(path)
    if out.returncode != 0 or out.stdout.lstrip().startswith("QUERY ERROR"):
        sys.exit("hana-sql failed:\n" + (out.stdout or "") + (out.stderr or ""))
    return list(csv.DictReader(out.stdout.splitlines()))


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def compute(rows, litres_per_pc=None, net_of_returns=True):
    litres_per_pc = litres_per_pc or {}
    out = []
    for r in rows:
        code = r["ItemCode"]
        oih, gross, ret = f(r["OIH"]), f(r["SOLD_GROSS"]), f(r["RETURNED"])
        fg, wip = f(r["FG_ONHAND"]), f(r["OPEN_PROD"])
        sold = gross - ret if net_of_returns else gross
        msl = max(0.0, MSL_PCT * sold)
        req = max(0.0, oih + msl - fg - wip)          # floored at zero
        lpp = litres_per_pc.get(code) or f(r["LTR_PER_PC"])
        out.append(dict(code=code, name=r["ItemName"], group=r["U_Sub_Group"],
                        oih=oih, sold=sold, msl=msl, fg=fg, wip=wip,
                        required_pcs=req, litres_per_pc=lpp, required_litres=req * lpp))
    out.sort(key=lambda x: -x["required_litres"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="sales month for MSL, YYYY-MM (default: previous calendar month)")
    ap.add_argument("--env", help="hana.env path (use a tunnelled one when the SAP ports are blocked)")
    ap.add_argument("--gross", action="store_true", help="MSL on gross sales instead of net of returns")
    ap.add_argument("--csv", help="write full result to this CSV")
    a = ap.parse_args()

    if a.month:
        y, m = (int(x) for x in a.month.split("-"))
        m0 = date(y, m, 1).isoformat()
        m1 = (date(y + (m == 12), (m % 12) + 1, 1)).isoformat()
    else:
        m0, m1 = prev_month_bounds(date.today())

    wip_cut = date.fromordinal(date.today().toordinal() - WIP_MAX_AGE_DAYS).isoformat()
    sql = SQL.format(co=CO, m0=m0, m1=m1, wip=wip_cut,
                     whs=",".join("'%s'" % w for w in FG_WAREHOUSES))
    rows = run_sql(sql, a.env)
    res = compute(rows, net_of_returns=not a.gross)

    tot_pcs = sum(r["required_pcs"] for r in res)
    tot_l = sum(r["required_litres"] for r in res)
    print(f"MSL month {m0} .. {m1}   |   FG godowns {'+'.join(FG_WAREHOUSES)}   |   "
          f"MSL {'gross' if a.gross else 'net of returns'}")
    print(f"SKUs needing production: {sum(1 for r in res if r['required_pcs'] > 0)} of {len(res)}")
    print(f"TOTAL REQUIRED: {tot_pcs:,.0f} bottles   {tot_l:,.0f} L   ({tot_l/1000:,.0f} MT)\n")
    print(f"{'CODE':<11}{'SKU':<44}{'OIH':>9}{'MSL':>9}{'FG':>9}{'WIP':>8}{'REQD':>10}{'LITRES':>11}")
    for r in res[:30]:
        if r["required_pcs"] <= 0:
            continue
        print(f"{r['code']:<11}{r['name'][:43]:<44}{r['oih']:>9,.0f}{r['msl']:>9,.0f}"
              f"{r['fg']:>9,.0f}{r['wip']:>8,.0f}{r['required_pcs']:>10,.0f}{r['required_litres']:>11,.0f}")

    if a.csv:
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(res[0].keys()))
            w.writeheader()
            w.writerows(res)
        print(f"\nwrote {a.csv}")


if __name__ == "__main__":
    main()
