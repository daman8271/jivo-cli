#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""demand_baseline_sap.py — the expected GT/MT demand, from three months of SAP billing.

    cd jolly && python3 live/demand_baseline_sap.py                 # pull from HANA, write live/state/demand_baseline.json
    cd jolly && python3 live/demand_baseline_sap.py --from-csv inv.csv cn.csv   # rebuild from CSVs already pulled
    cd jolly && python3 live/demand_baseline_sap.py --months 3 --to 2026-08-31  # window end (default: last day of last month)

RULING (Mark 4 rulebook R17/R18/A09, meeting 10:19-11:02, Daman 2026-09-06): production
planning predicts the month's GT/MT orders from PAST GT/MT SALES, excluding e-commerce,
because GT/MT bunches its orders in the last weeks of the month and a PO-only plan runs the
buffer dry. This is THE ONE allowed SAP read in the live planner (billing history is the
only complete 3-month record; OMS history before 2026-09-02 is not backfilled). Everything
about the factory still comes from ji.jivo.in (RULE 0).

RUN IT DAILY, NOT EVERY 3 MINUTES. It reads HANA through hana-sql (read-only, guarded); on
the VPS `connections/hana-vps-direct.env` answers directly; on a Mac it falls back to
`ssh vps`. The 3-minute chain (live/loop.sh) only READS the file this writes; when the file
is missing the freeze falls back to the plan sheet's own forecast and says so in honesty.

WHAT IT WRITES  live/state/demand_baseline.json, adapter-shaped (live/README.md contract):
    data.window            {from, to, months}
    data.channels_included ["GT","MT","ROI","CORPORATE","HORECA","CSD","REFERENCE"]  (A17: "GT/MT" =
                           every outside channel except e-commerce; OCRD.U_Main_Group is the channel field)
    data.channels_excluded ["E-COMMERCE","BRANCH","STAFF","CASH SALE","(blank)"]
    data.intercompany_excluded  the 9 Oil group cards (harness correction C-0005)
    data.by_channel        {main_group: {litres, inr, lines}}  over the window, AFTER the exclusions
    data.excluded_totals   {main_group_or_card: {litres, inr}} what was left out, so the choice is visible
    data.week_of_month     {"1".."5": {days, litres, litres_per_day, share}}  bucket 1 = days 1-7 ... 5 = days 29-31
    data.skus              {ItemCode: {name, sku, type, sub_group, litres_per_month, inr_per_month, pieces_per_month,
                                       months_seen, by_month{YYYY-MM: litres}, by_week{1..5: litres}, by_channel{mg: litres},
                                       rank, in_plan_sheet}}
    data.totals            {litres, inr, lines, skus, skus_in_plan_sheet, skus_not_in_plan_sheet, litres_not_in_plan_sheet}
    data.basis             the exact definition (net of GST, credit notes netted, pieces x pack litres from OITM.U_SKU)
Litres: INV1.Quantity is PIECES (correction C-0001); litres = pieces x engine.plan_units.pack_litres(OITM.U_SKU)
— the only sanctioned pack parser; KGS packs are weight / 0.91. Credit notes (ORIN/RIN1) are subtracted.
"""
import argparse, csv, io, json, os, subprocess, sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOLLY = HERE.parent
REPO = JOLLY.parent
sys.path.insert(0, str(JOLLY))
from engine.plan_units import pack_litres   # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
CO = "JIVO_OIL_HANADB"
INCLUDED = ["GT", "MT", "ROI", "CORPORATE", "HORECA", "CSD", "REFERENCE"]
EXCLUDED_MG = ["E-COMMERCE", "BRANCH", "STAFF", "CASH SALE", "(blank)"]
INTERCO = ["CUSTA000001", "CUSTA000002", "CUSTA000003", "CUSTA000004", "CUSTA000606",
           "CUSTA000827", "CUSTA000906", "CUSTA001099", "CUSTA001113"]          # C-0005, Oil book
OUT = JOLLY / "live/state/demand_baseline.json"

SQL = """SELECT L."ItemCode" IC, I."ItemName" NM, I."U_SKU" SKU, I."U_TYPE" TY, I."U_Sub_Group" SG,
       IFNULL(C."U_Main_Group",'(blank)') MG, H."CardCode" CC, TO_VARCHAR(H."DocDate",'YYYY-MM') YM,
       CASE WHEN DAYOFMONTH(H."DocDate")<=7 THEN 1 WHEN DAYOFMONTH(H."DocDate")<=14 THEN 2 WHEN DAYOFMONTH(H."DocDate")<=21 THEN 3 WHEN DAYOFMONTH(H."DocDate")<=28 THEN 4 ELSE 5 END WK,
       SUM(L."Quantity") PCS, SUM(L."LineTotal") INR, COUNT(*) N
FROM {co}.{H} H JOIN {co}.{L} L ON L."DocEntry"=H."DocEntry"
JOIN {co}.OCRD C ON C."CardCode"=H."CardCode" JOIN {co}.OITM I ON I."ItemCode"=L."ItemCode"
WHERE H."DocDate">='{d0}' AND H."DocDate"<'{d1}' AND H."CANCELED"='N' AND L."ItemCode" LIKE 'FG%'
GROUP BY L."ItemCode", I."ItemName", I."U_SKU", I."U_TYPE", I."U_Sub_Group", C."U_Main_Group", H."CardCode", TO_VARCHAR(H."DocDate",'YYYY-MM'),
       CASE WHEN DAYOFMONTH(H."DocDate")<=7 THEN 1 WHEN DAYOFMONTH(H."DocDate")<=14 THEN 2 WHEN DAYOFMONTH(H."DocDate")<=21 THEN 3 WHEN DAYOFMONTH(H."DocDate")<=28 THEN 4 ELSE 5 END"""

def hana_csv(sql):
    """Run one read-only statement through hana-sql; local env first, then ssh vps."""
    binp = REPO / "hana-sql" / "hana-sql"
    if os.uname().sysname == "Linux" and (REPO / "hana-sql" / "hana-sql.linux").exists():
        binp = REPO / "hana-sql" / "hana-sql.linux"
    for env in ([os.environ["HANA_ENV"] + ".env"] if os.environ.get("HANA_ENV") else []) + ["hana-vps-direct.env", "hana-office-bridge.env", "hana-new.env"]:
        envp = REPO / "connections" / env
        if not envp.exists(): continue
        r = subprocess.run([str(binp), "-env", str(envp), "-csv", sql], capture_output=True, text=True, timeout=180)
        if r.returncode == 0 and r.stdout.strip(): return r.stdout, f"hana-sql {env}"
    # a Mac cannot reach HANA without the tunnel — ask the VPS, which reads it directly
    r = subprocess.run(["ssh", "-o", "ConnectTimeout=10", "vps",
                        "cd /root/jivo-cli && ./hana-sql/hana-sql.linux -env connections/hana-vps-direct.env -csv \"$(cat)\""],
                       input=sql, capture_output=True, text=True, timeout=240)
    if r.returncode == 0 and r.stdout.strip(): return r.stdout, "ssh vps hana-sql hana-vps-direct.env"
    sys.exit(f"HANA unreachable: {r.stderr.strip()[:300]}")

def f(v):
    try: return float(v)
    except (TypeError, ValueError): return 0.0

def month_bounds(to_s, months):
    to = date.fromisoformat(to_s) if to_s else (date.today().replace(day=1) - timedelta(days=1))
    first_of_to = to.replace(day=1)
    d0 = first_of_to
    for _ in range(months - 1):
        d0 = (d0 - timedelta(days=1)).replace(day=1)
    return d0, to + timedelta(days=1)   # [d0, d1)

def week_days(d0, d1):
    days = defaultdict(int); d = d0
    while d < d1:
        wk = 1 if d.day <= 7 else 2 if d.day <= 14 else 3 if d.day <= 21 else 4 if d.day <= 28 else 5
        days[str(wk)] += 1; d += timedelta(days=1)
    return dict(days)

def build(inv_rows, cn_rows, d0, d1, months, plan_codes, pulled_via):
    skus = {}; by_ch = defaultdict(lambda: dict(litres=0.0, inr=0.0, lines=0)); excl = defaultdict(lambda: dict(litres=0.0, inr=0.0))
    wk_l = defaultdict(float); unparsed = defaultdict(float)
    tot = dict(litres=0.0, inr=0.0, lines=0)
    def take(rows, sign):
        for r in rows:
            pcs, inr, n = sign * f(r["PCS"]), sign * f(r["INR"]), int(f(r["N"]))
            lit, how = pack_litres(r["SKU"] or r["NM"])
            if lit is None:
                lit2, how2 = pack_litres(r["NM"])
                lit = lit2
            if lit is None:
                unparsed[r["IC"] + " " + r["NM"]] += pcs; lit = 0.0
            litres = pcs * lit
            mg = r["MG"] or "(blank)"
            if mg in EXCLUDED_MG or r["CC"] in INTERCO:
                key = r["CC"] if r["CC"] in INTERCO else mg
                excl[key]["litres"] += litres; excl[key]["inr"] += inr
                continue
            by_ch[mg]["litres"] += litres; by_ch[mg]["inr"] += inr; by_ch[mg]["lines"] += n
            tot["litres"] += litres; tot["inr"] += inr; tot["lines"] += n
            wk_l[r["WK"]] += litres
            s = skus.setdefault(r["IC"], dict(name=r["NM"], sku=r["SKU"], type=r["TY"], sub_group=r["SG"], litres_per_piece=lit,
                                              by_month=defaultdict(float), by_week=defaultdict(float), by_channel=defaultdict(float),
                                              pieces=0.0, litres=0.0, inr=0.0))
            s["by_month"][r["YM"]] += litres; s["by_week"][r["WK"]] += litres; s["by_channel"][mg] += litres
            s["pieces"] += pcs; s["litres"] += litres; s["inr"] += inr
    take(inv_rows, +1); take(cn_rows, -1)
    days = week_days(d0, d1)
    wk = {k: dict(days=days.get(k, 0), litres=round(wk_l.get(k, 0.0)), litres_per_day=round(wk_l.get(k, 0.0) / days[k]) if days.get(k) else None,
                  share=round(wk_l.get(k, 0.0) / tot["litres"], 4) if tot["litres"] else None) for k in ["1", "2", "3", "4", "5"]}
    out = {}
    ranked = sorted(skus.items(), key=lambda kv: -kv[1]["litres"])
    for rank, (code, s) in enumerate(ranked, 1):
        out[code] = dict(name=s["name"], sku=s["sku"], type=s["type"], sub_group=s["sub_group"], litres_per_piece=s["litres_per_piece"],
                         litres_per_month=round(s["litres"] / months), inr_per_month=round(s["inr"] / months), pieces_per_month=round(s["pieces"] / months),
                         months_seen=len([m for m, v in s["by_month"].items() if v > 0]),
                         by_month={m: round(v) for m, v in sorted(s["by_month"].items())},
                         by_week={k: round(s["by_week"].get(k, 0.0)) for k in ["1", "2", "3", "4", "5"]},
                         by_channel={k: round(v) for k, v in sorted(s["by_channel"].items(), key=lambda kv: -kv[1])},
                         rank=rank, in_plan_sheet=code in plan_codes)
    not_in = [c for c in out if c not in plan_codes]
    return dict(
        company=CO, window=dict(**{"from": d0.isoformat(), "to": (d1 - timedelta(days=1)).isoformat()}, months=months),
        channel_field="OCRD.U_Main_Group (the party's channel, inherited by every sale line)",
        channels_included=INCLUDED, channels_excluded=EXCLUDED_MG, intercompany_excluded=INTERCO,
        by_channel={k: dict(litres=round(v["litres"]), inr=round(v["inr"]), lines=v["lines"]) for k, v in sorted(by_ch.items(), key=lambda kv: -kv[1]["litres"])},
        excluded_totals={k: dict(litres=round(v["litres"]), inr=round(v["inr"])) for k, v in sorted(excl.items(), key=lambda kv: -kv[1]["inr"])},
        week_of_month=wk,
        skus=out,
        totals=dict(litres=round(tot["litres"]), inr=round(tot["inr"]), lines=tot["lines"], skus=len(out),
                    skus_in_plan_sheet=sum(1 for c in out if c in plan_codes), skus_not_in_plan_sheet=len(not_in),
                    litres_not_in_plan_sheet=round(sum(skus[c]["litres"] for c in not_in)),
                    litres_per_month=round(tot["litres"] / months), inr_per_month=round(tot["inr"] / months)),
        unparsed_packs={k: round(v) for k, v in unparsed.items()},
        basis=("SAP OINV/INV1 (invoices) minus ORIN/RIN1 (credit notes), Oil book, DocDate in window, CANCELED='N', FG items; "
               "INR = INV1.LineTotal net of GST (never header DocTotal); litres = INV1.Quantity (PIECES, C-0001) x pack litres parsed "
               "from OITM.U_SKU by engine/plan_units.pack_litres (KGS / 0.91). Channel = OCRD.U_Main_Group; e-commerce, branches, staff, "
               "cash sales and the 9 Oil intercompany cards (C-0005) excluded — the excluded totals are published beside the included."),
        pulled_via=pulled_via, rulebook=["R17", "R18", "A09", "A17"])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=3)
    ap.add_argument("--to", default=None, help="last day of the window, YYYY-MM-DD (default: last day of last month)")
    ap.add_argument("--from-csv", nargs=2, metavar=("INV_CSV", "CN_CSV"))
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    d0, d1 = month_bounds(a.to, a.months)
    if a.from_csv:
        inv = list(csv.DictReader(open(a.from_csv[0], encoding="utf-8"))); cn = list(csv.DictReader(open(a.from_csv[1], encoding="utf-8")))
        via = f"csv {a.from_csv[0]} + {a.from_csv[1]}"
    else:
        inv_txt, via = hana_csv(SQL.format(co=CO, H="OINV", L="INV1", d0=d0.isoformat(), d1=d1.isoformat()))
        cn_txt, _ = hana_csv(SQL.format(co=CO, H="ORIN", L="RIN1", d0=d0.isoformat(), d1=d1.isoformat()))
        inv = list(csv.DictReader(io.StringIO(inv_txt))); cn = list(csv.DictReader(io.StringIO(cn_txt)))
    plan_codes = set()
    for p in ("sim/live-inputs.json", "sim/sep-inputs.json"):
        try:
            plan_codes = {r["code"] for r in json.load(open(JOLLY / p))["plan"]}; break
        except Exception: continue
    data = build(inv, cn, d0, d1, a.months, plan_codes, via)
    now = datetime.now(IST).isoformat(timespec="seconds")
    doc = dict(source="demand_baseline", fetched_at=now, server_at=None, ok=True, error=None, data=data)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    t = data["totals"]
    print(f"wrote {a.out}: {t['skus']} SKUs, {t['litres']:,} L, Rs {t['inr']/1e7:,.2f} Cr over {a.months} months ({data['window']['from']} → {data['window']['to']}); "
          f"{t['skus_in_plan_sheet']} on the plan sheet, {t['skus_not_in_plan_sheet']} not ({t['litres_not_in_plan_sheet']:,} L); via {via}")
    print("by channel:", {k: f"{v['litres']:,} L" for k, v in data["by_channel"].items()})
    print("excluded:", {k: f"Rs {v['inr']/1e7:.2f} Cr" for k, v in list(data["excluded_totals"].items())[:6]})
    print("week of month (L/day):", {k: v["litres_per_day"] for k, v in data["week_of_month"].items()})
    if data["unparsed_packs"]: print("UNPARSED packs (0 litres counted):", data["unparsed_packs"])

if __name__ == "__main__":
    main()
