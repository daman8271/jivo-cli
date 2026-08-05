#!/usr/bin/env python3
"""build_data.py — daily-refresh engine for the JIVO godown dashboard.

Runs the 9 extraction .sql files against SAP HANA via the read-only hana-sql
CLI, computes company-item stock metrics, and emits site/data.json (minified).
Deterministic, stdlib-only, safe to run unattended (cron).

Exit codes: 0 ok, 1 connection/SQL failure or sanity-guard refusal.
"""
import json
import math
import os
import re
import shlex
import statistics
import subprocess
import sys
from datetime import datetime, date, timedelta

# Overridable for other machines (VPS, cron hosts). Defaults = this Mac.
#   HANA_SQL_BIN     path to the read-only hana-sql CLI binary
#   HANA_ENV_FILE    -env file used for the tunnel route
#   HANA_TUNNEL_CMD  full tunnel command as ONE shell string (shlex-split here)
HANA_SQL = os.environ.get(
    "HANA_SQL_BIN", "/Users/damanpreetsingh/jivo-cli/hana-sql/hana-sql")
HANA_DIR = os.path.dirname(HANA_SQL)
TUNNEL_ENV = os.environ.get(
    "HANA_ENV_FILE", "/Users/damanpreetsingh/jivo-cli/connections/hana-tunnel.env")
# Fallback route. Hops through the VPS, NOT through jivo-sap-any: off the office
# network the SAP box is unreachable directly (verified dead 2026-08-03), while
# the VPS stays connected because SAP parks a reverse tunnel on it and serves
# HANA at the VPS's own 127.0.0.1:47301. Production overrides this with
# HANA_TUNNEL_CMD=true (the VPS is already at the endpoint).
TUNNEL_CMD = shlex.split(os.environ.get(
    "HANA_TUNNEL_CMD",
    "ssh -f -N -o ExitOnForwardFailure=yes -L 13015:127.0.0.1:47301 vps"))
PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(os.path.dirname(PIPELINE_DIR), "site")
OUT_PATH = os.path.join(SITE_DIR, "data.json")

COMPANIES = [
    ("oil", "JIVO Oil", "JIVO_OIL_HANADB"),
    ("mart", "JIVO Mart", "JIVO_MART_HANADB"),
    ("bev", "JIVO Beverages", "JIVO_BEVERAGES_HANADB"),
]
QUERIES = ("stock", "velocity", "history")

# ---------------------------------------------------------------- connection

_ENV_ARGS = None  # set once by connect(): [] for direct, ["-env", ...] for tunnel


def _run_hana(sql, env_args, timeout=300):
    """Run one SQL statement through hana-sql; return stdout or raise."""
    cmd = [HANA_SQL] + env_args + [sql]
    p = subprocess.run(cmd, cwd=HANA_DIR, capture_output=True, text=True,
                       timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "hana-sql exited %d" % p.returncode)
    return p.stdout


def connect():
    """Probe direct route; on failure raise the home tunnel and retry."""
    global _ENV_ARGS
    probe = 'SELECT 1 AS "OK" FROM DUMMY'
    try:
        _run_hana(probe, [], timeout=30)
        _ENV_ARGS = []
        print("connection: direct (office route)")
        return
    except Exception as e:
        print("direct route failed (%s); trying home tunnel..." % e)
    # Ensure the tunnel; ignore failure (port may already be bound).
    try:
        subprocess.run(TUNNEL_CMD, capture_output=True, text=True, timeout=30)
    except Exception:
        pass
    try:
        _run_hana(probe, ["-env", TUNNEL_ENV], timeout=30)
        _ENV_ARGS = ["-env", TUNNEL_ENV]
        print("connection: home tunnel (port 13015 via jivo-sap-any)")
        return
    except Exception as e:
        sys.exit("FATAL: no route to HANA. Direct probe failed and the home "
                 "tunnel route failed too (%s). Check office wifi or "
                 "`ssh jivo-sap-any`." % e)


def read_sql(path):
    """Read SQL text, dropping leading '--' comment lines (hana-sql would
    misparse an argv starting with '--' as a CLI flag)."""
    with open(path) as f:
        lines = f.read().splitlines()
    while lines and (not lines[0].strip() or lines[0].lstrip().startswith("--")):
        lines.pop(0)
    return "\n".join(lines).strip()


def fetch(name):
    """Run <name>.sql, return list of dict rows parsed from TSV."""
    sql = read_sql(os.path.join(PIPELINE_DIR, name + ".sql"))
    out = _run_hana(sql, _ENV_ARGS)
    lines = out.splitlines()
    if not lines:
        raise RuntimeError("%s: empty result" % name)
    hdr = lines[0].split("\t")
    rows = [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:] if ln]
    print("  %-14s %6d rows" % (name, len(rows)))
    return rows


# ------------------------------------------------------------------ helpers

def num(v):
    if v is None or v in ("", "NULL", "?"):
        return 0.0
    try:
        return float(v)
    except ValueError:
        return 0.0


def txt(v):
    """Normalize the three blank encodings ('', ' ', 'NULL') to ''."""
    if v is None:
        return ""
    v = v.strip()
    return "" if v.upper() == "NULL" else v


def rnd(x, nd=2):
    r = round(x, nd)
    return int(r) if r == int(r) else r


def classify(code, name):
    """Warehouse class from code+name tokens (order matters)."""
    c = (code or "").upper()
    n = (name or "").upper()
    toks = set(c.replace("-", " ").split()) | set(
        n.replace("-", " ").replace("(", " ").replace(")", " ").split())
    ctoks = set(c.replace("-", " ").split())
    if "FA" in ctoks or "FIXED ASSET" in n or "FIXED ASSTES" in n:
        return "fixed-assets"
    if "INT" in ctoks or "INTRANSIT" in n or "INTRASIT" in n or "INSTRASIT" in n:
        return "in-transit"
    if c.startswith("DP-") or "DP" in ctoks or "DROPSHIP" in n or "DRP" in toks:
        return "dropship"
    if "WST" in ctoks or "WASTAGE" in n:
        return "wastage"
    if "NM" in ctoks or "NON-MOVING" in n or "NON MOVING" in n:
        return "non-moving"
    if "VIRTUAL" in n or "VG" in ctoks or "GG" in ctoks:
        return "virtual"
    if "ISD" in ctoks or "POP" in ctoks or "PAPER MEDIA" in n or "PRESHIT" in n:
        return "other-media"
    return "physical"


# -------------------------------------------------------------- unit weight

# kg per one inventory unit ("kgpu"), or None when no honest number exists.
# Tonnage is approximate by design: litres convert at oil density 0.91 kg/L,
# water/beverages at 1.0. Packaging and machinery NEVER get weight — a
# "LABEL 250 MLS APPLE" weighs ~1 g and a "TANK 90 LTR" is capacity, not
# content. When in doubt: None (no tonnage) beats a guess.

DENSITY_OIL = 0.91
DENSITY_WATER = 1.0

# UoMs whose stock quantity already IS a weight/volume.
_UOM_KG = {"KGS": 1.0, "KG": 1.0, "GMS": 0.001, "GM": 0.001,
           "MTS": 1000.0, "MT": 1000.0, "TON": 1000.0}
_UOM_LITRE = {"LTR", "L"}
_UOM_PIECE = {"PCS", ""}

# First "<number> <unit>" in the item name = one bottle's content (quantities
# are bottles per correction C-0001). Trailing carton counts like "20 PCS"
# never match because PCS is not a unit here. Longest alternatives first so
# LTR wins over LT and MLS over ML.
# "L" is last so LTR/LITRE/LT still win; without it "RICE BRAN 1L 16 PCS" and
# "SANO POMACE OLIVE OIL 15 L" parsed to nothing and carried no tonnage at all.
# Verified over all 2,505 live items: adding it changes exactly 5 names, 3 of
# them finished oils that should be weighed and 2 fixed assets that the FA
# prefix/group already refuses before this regex is ever reached.
_PACK_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(LITRE|LTR|LT|MLS|ML|KGS|KG|GMS|GM|L)\b")

_WATERY = re.compile(
    r"\b(WATER|MINERAL|JUICE|SODA|DRINK|SHIKANJI|JEERA|MOJITO|MANGO)\b")
# Packaging/consumable/asset words: these items wrap or make the product, so
# their name-sizes describe someone else's content.
_PACKW = re.compile(
    r"\b(LABEL|CARTON|BOTTLE|CAP|CAPS|SHRINK|PREFORM|TAPE|WRAPPER|HANDLE"
    r"|PUMP|STICKER|POUCH|BOX)\b")
# Groups whose token-bearing names are FILLED product, not empty packaging
# ("SOYABEAN OIL 1 LTR POUCH 12 PCS" is oil, not a pouch); everywhere else
# (trading merch, consumables) a BOTTLE in the name is an empty bottle.
_FILLED_GRPS = {"FINISHED", "SEMI FINISHED GOODS", "RAW MATERIAL"}
# Vessels that are NEVER filled product here, whatever their group says. Unlike
# POUCH or JAR — "SOYABEAN OIL 1 LTR POUCH" and "WHEAT GRASS POWDER JAR 150
# GMS" really are goods — a FLASK at JIVO is branded steel merchandise
# (TRADING ITEMS) and a BEAKER is lab glassware (RAW MATERIAL). Both groups sit
# in _FILLED_GRPS, so the packaging-word check below never sees them and their
# "1000 MLS" was being read as 910 g of oil. Small (~1.4 T) but plainly wrong.
_VESSELW = re.compile(r"\b(FLASK|BEAKER)\b")
_EXCL_GRP = ("PACKAG", "FIXED ASSET", "CONSUMABLE", "LABORATORY")
_EXCL_PREFIX = ("PM", "FA", "EX", "LB")


def unit_kg(co, code, name, grp, uom, variety):
    """kg per one inventory unit, or None. Deterministic, no I/O."""
    name = (name or "").upper()
    grp = (grp or "").upper()
    uom = (uom or "").strip().upper()
    # hard exclusions first: packaging, machinery, consumables, lab gear
    if code[:2] in _EXCL_PREFIX:
        return None
    if any(t in grp for t in _EXCL_GRP):
        return None
    if _VESSELW.search(name):
        return None
    if grp not in _FILLED_GRPS and _PACKW.search(name):
        return None
    # density: water/beverage names, any bev finished drink, and the
    # "PET/GLASS BOTTLE ..." finished-drink naming scheme are 1.0 kg/L
    watery = (bool(_WATERY.search(name + " " + (variety or "").upper()))
              or (co == "bev" and grp == "FINISHED")
              or name.startswith(("PET BOTTLE", "GLASS BOTTLE")))
    dens = DENSITY_WATER if watery else DENSITY_OIL
    if uom in _UOM_KG:
        return _UOM_KG[uom]
    if uom in _UOM_LITRE:
        return dens
    if uom in _UOM_PIECE:
        m = _PACK_RE.search(name)
        if not m:
            return None
        n, u = float(m.group(1)), m.group(2)
        if u in ("LITRE", "LTR", "LT", "L"):
            return n * dens
        if u in ("MLS", "ML"):
            return n * dens / 1000.0
        return n * _UOM_KG[u]
    return None  # UNT / DRM / MTR / NOS / SET / MLS-as-UoM: no honest weight


# ---------------------------------------------------------------- big-3 sites

# SAP's 135 warehouse codes collapse into ~14 real places, and three hold
# ~97% of book value (verified against live data 2026-08-02). Everything
# else is small partner/agent premises (C&F, Flipkart FBF, job-workers,
# cold storage) and goes in the "other" bucket.
SITE_DEFS = [
    # Places are SAP's own, from OWHS City/State (verified 2026-08-03):
    # BH-* = 27 Sonipat + 1 Jhajjar (BH-LR, excluded below), GP-* = 4 Sonipat,
    # DL-*/MY-* = New Delhi. Bhakharpur and Gupta share one Sonipat address
    # (Khasra No 20//9/2 & 10/1/2, 131101) — they are adjacent, not in Delhi.
    ("bhakharpur", "Bhakharpur plant complex (Sonipat, HR)"),
    ("gupta", "Gupta godown (Sonipat, HR)"),
    ("mayapuri", "Mayapuri, New Delhi"),
    ("other", "Partner & other premises"),
]

# BH-coded warehouses that are NOT physically at the Bhakharpur plant.
_NOT_BHAKHARPUR = {
    "BH-LR",     # Luhari Jhajjar
    "BH-SN",     # Shanti Cold Storage (third party)
    "BH-CRUDE",  # Gujarat crude
    "BH-GJ",     # Gujarat job-worker
}


def site_of(code):
    """Collapse one warehouse code into a real place. Deterministic."""
    c = (code or "").upper()
    if c.startswith("BH") and c not in _NOT_BHAKHARPUR:
        return "bhakharpur"
    if c.startswith("GP"):
        return "gupta"
    if (c.startswith("DL") or c.startswith("MY-")) and c != "DL-J3":
        return "mayapuri"
    return "other"


def build_sites(godowns, items):
    """Roll godowns up into the big-3 sites + other.

    value      = SAP book value of every code at the site (all companies)
    fa_value   = value sitting in fixed-assets-class codes (machinery
                 booked as stock — not goods)
    goods_value= value - fa_value
    items      = distinct item records (per company) actually holding
                 stock in the site's non-fixed-assets codes
    """
    sites = {name: {"name": name, "label": label, "codes": [],
                    "value": 0.0, "goods_value": 0.0, "fa_value": 0.0,
                    "items": 0, "tonnes": 0.0, "_tnum": 0.0, "_tden": 0.0}
             for name, label in SITE_DEFS}
    fa_keys = set()
    for g in godowns:
        s = sites[site_of(g["code"])]
        key = g["co"] + "|" + g["code"]
        s["codes"].append(key)
        s["value"] += g["value"]
        if g["class"] == "fixed-assets":
            s["fa_value"] += g["value"]
            fa_keys.add(key)
    stocked = {name: set() for name, _ in SITE_DEFS}
    for it in items:
        kgpu = it.get("kgpu")
        for w in it.get("whs", ()):
            key = it["co"] + "|" + w["w"]
            if key in fa_keys:
                continue
            s = sites[site_of(w["w"])]
            if w["q"] > 0:
                stocked[s["name"]].add(it["co"] + "|" + it["code"])
            # coverage over POSITIVE value only (negative cost pools would
            # otherwise push the ratio past 100%)
            s["_tden"] += max(w["v"], 0)
            if kgpu is not None:
                s["tonnes"] += w["q"] * kgpu / 1000.0
                s["_tnum"] += max(w["v"], 0)
    out = []
    for name, _ in SITE_DEFS:
        s = sites[name]
        s["codes"].sort()
        s["goods_value"] = rnd(s["value"] - s["fa_value"], 0)
        s["value"] = rnd(s["value"], 0)
        s["fa_value"] = rnd(s["fa_value"], 0)
        s["items"] = len(stocked[name])
        s["tonnes"] = rnd(s["tonnes"], 1)
        s["t_coverage_pct"] = rnd(100.0 * s["_tnum"] / s["_tden"], 0) if s["_tden"] > 0 else 0
        del s["_tnum"], s["_tden"]
        out.append(s)
    return out


# ------------------------------------------------------------------- expiry

def build_expiry(prefix):
    """Batch-expiry rollup for one company from <prefix>_expiry.sql.

    Only batches carrying a recorded ExpDate can be judged; a company where
    zero batches have one is reported tracked=False (Mart, verified live) —
    its real expired stock is unknown, not zero. Quantities are in each
    item's own inventory UoM (some are grams), so top rows carry "uom"."""
    rows = fetch(prefix + "_expiry")
    today = date.today()
    soon = today + timedelta(days=90)
    dated = 0
    exp_by_uom = {}
    soon_by_uom = {}
    per = {}
    for r in rows:
        ed = txt(r.get("ExpDate", ""))[:10]
        if not ed:
            continue
        dated += 1
        try:
            d = datetime.strptime(ed, "%Y-%m-%d").date()
        except ValueError:
            continue
        q = num(r["Quantity"])
        u = txt(r["InvntryUom"]) or "units"
        if d < today:
            exp_by_uom[u] = exp_by_uom.get(u, 0.0) + q
            e = per.setdefault(r["ItemCode"], {
                "code": r["ItemCode"], "name": txt(r["ItemName"]),
                "uom": u, "qty": 0.0, "exp": ed})
            e["qty"] += q
            if ed < e["exp"]:
                e["exp"] = ed
        elif d < soon:
            soon_by_uom[u] = soon_by_uom.get(u, 0.0) + q
    if not dated:
        return {"tracked": False}
    top = sorted(per.values(), key=lambda e: -e["qty"])[:8]
    for e in top:
        e["qty"] = rnd(e["qty"])

    def _by_uom(d):
        return {u: rnd(v) for u, v in sorted(d.items(), key=lambda kv: -kv[1])}

    out = {"tracked": True, "expired_items": len(per), "top": top,
           "expired_by_uom": _by_uom(exp_by_uom),
           "expiring90_by_uom": _by_uom(soon_by_uom)}
    # A single expired-quantity number is only a quantity when every expired
    # batch shares one unit. Beverages does NOT: its batches are 334,335 GMS +
    # 201,251 MLS + 34,238 PCS + 1,376 LTR + 360 KGS + 6.28 UNT, and adding
    # grams to millilitres to bottles produced a headline "571,567 expired"
    # that is not a quantity of anything. So publish the scalar only when the
    # units agree (oil: all PCS); otherwise the per-UoM split is the answer.
    for src, qk, uk in ((exp_by_uom, "expired_qty", "expired_uom"),
                        (soon_by_uom, "expiring90_qty", "expiring90_uom")):
        if len(src) == 1:
            out[qk] = rnd(sum(src.values()))
            out[uk] = next(iter(src))
    return out


# -------------------------------------------------------------------- build

def build_company(key, label, schema):
    prefix = {"oil": "oil", "mart": "mart", "bev": "bev"}[key]
    stock = fetch(prefix + "_stock")
    velocity = fetch(prefix + "_velocity")
    history = fetch(prefix + "_history")

    # index velocity / history by (item, whs)
    vel = {(r["ItemCode"], r["Warehouse"]):
           (num(r["OUT90"]), num(r["RET90"])) for r in velocity}
    hist = {(r["ItemCode"], r["Warehouse"]):
            [num(r["NET_AFTER_%d" % i]) for i in range(1, 7)] for r in history}

    # pair-level stock + item attributes
    items = {}           # code -> attrs
    pairs = {}           # (code, whs) -> [onhand, commit, onorder, value]
    whs_meta = {}        # whs code -> name
    for r in stock:
        ic, wc = r["ItemCode"], r["WhsCode"]
        whs_meta.setdefault(wc, txt(r["WhsName"]))
        items.setdefault(ic, {
            "name": txt(r["ItemName"]), "grp": txt(r["ItmsGrpNam"]),
            "uom": txt(r["InvntryUom"]), "utype": txt(r["U_TYPE"]),
            "variety": txt(r["U_Sub_Group"]),
            "frozen": txt(r["frozenFor"]) == "Y",
        })
        pairs[(ic, wc)] = [num(r["OnHand"]), num(r["IsCommited"]),
                           num(r["OnOrder"]), num(r["StockValue"])]

    # godown + company value rollups. Value sums ALL pools (including
    # zero-quantity cost-pool rows and negatives) so the totals equal SAP's
    # own net stock value; item counts only count rows actually holding stock.
    god = {}   # whs -> {value, items}
    total_value = 0.0
    physical_value = 0.0
    for (ic, wc), (oh, cm, oo, sv) in pairs.items():
        g = god.setdefault(wc, {"value": 0.0, "items": 0})
        g["value"] += sv
        total_value += sv
        if classify(wc, whs_meta.get(wc, "")) == "physical":
            physical_value += sv
        if oh > 0:
            g["items"] += 1

    # per-item aggregation (union of stock/velocity/history pairs per item)
    item_whs = {}
    for (ic, wc) in list(pairs) + list(vel) + list(hist):
        if ic in items:                       # item universe = stock items
            item_whs.setdefault(ic, set()).add(wc)

    wcls = {}                                 # memoised warehouse class

    def _cls(wc):
        if wc not in wcls:
            wcls[wc] = classify(wc, whs_meta.get(wc, ""))
        return wcls[wc]

    out_items = []
    status_counts = {}
    listed_value = 0.0
    tonnes = 0.0                              # company goods weight
    cov_num = cov_den = 0.0                   # t-coverage by goods value
    for ic, attrs in items.items():
        onhand = commit = onorder = value = out90 = 0.0
        goods_v = 0.0                         # value outside fixed-assets whs
        levels = [0.0] * 6
        whs_list = []
        for wc in sorted(item_whs.get(ic, ())):
            oh, cm, oo, sv = pairs.get((ic, wc), (0.0, 0.0, 0.0, 0.0))
            onhand += oh; commit += cm; onorder += oo; value += sv
            if _cls(wc) != "fixed-assets":
                goods_v += sv
            o90, r90 = vel.get((ic, wc), (0.0, 0.0))
            out90 += max(o90 - min(r90, o90), 0.0)
            net = hist.get((ic, wc), [0.0] * 6)
            for i in range(6):
                levels[i] += oh - net[i]
            if oh != 0 or sv != 0:
                whs_list.append({"w": wc, "q": rnd(oh), "v": rnd(sv, 0)})
        daily_rate = out90 / 90.0
        cover = (onhand / daily_rate) if daily_rate > 0 else None
        hist_avg = statistics.mean(levels)
        # "Normal" needs a baseline to be normal AGAINST. An item first stocked
        # inside the 6-month window has zeros at the month-ends before it
        # existed, so the mean is diluted by months it was never there and the
        # comparison explodes: a brand-new item reconstructs as levels
        # [0,0,0,0,0,X], mean X/6, and lands on exactly +500% "overstock" when
        # in truth it has no history at all. The artefact is exact and general —
        # k months of history always yields (6-k)/k*100%. Quote a comparison
        # only when at least half the window carries stock; otherwise emit
        # nothing and flag the item new, so the board shows "new" and not a
        # fabricated overstock figure.
        months_with_stock = sum(1 for lv in levels if lv > 0.001)
        has_baseline = hist_avg > 0.001 and months_with_stock >= 3
        vs_normal = ((onhand - hist_avg) / hist_avg * 100.0) if has_baseline else None

        if onhand <= 0 and daily_rate == 0:
            continue                          # dead-and-empty: omit entirely
        if onhand <= 0 and daily_rate > 0:
            status = "OUT"
        elif onhand > 0 and daily_rate == 0:
            status = "DEAD"
        elif cover < 15:
            status = "LOW"
        elif cover > 60:
            status = "HIGH"
        else:
            status = "NORMAL"
        status_counts[status] = status_counts.get(status, 0) + 1
        listed_value += value

        kgpu = unit_kg(key, ic, attrs["name"], attrs["grp"],
                       attrs["uom"], attrs["variety"])
        # coverage over POSITIVE goods value only — negative cost pools would
        # otherwise push the ratio past 100%
        cov_den += max(goods_v, 0.0)
        if kgpu is not None:
            tonnes += onhand * kgpu / 1000.0
            cov_num += max(goods_v, 0.0)

        rec = {"co": key, "code": ic, "name": attrs["name"],
               "grp": attrs["grp"], "uom": attrs["uom"],
               "onhand": rnd(onhand), "value": rnd(value, 0),
               "out90": rnd(out90, 1), "hist_avg": rnd(hist_avg, 1),
               "status": status, "whs": whs_list}
        if kgpu is not None:
            rec["kgpu"] = rnd(kgpu, 3)
            rec["t"] = rnd(onhand * kgpu / 1000.0, 2)
        if attrs["utype"]:
            rec["utype"] = attrs["utype"]
        if attrs["variety"]:
            rec["variety"] = attrs["variety"]
        if attrs["frozen"]:
            rec["frozen"] = 1
        if commit:
            rec["committed"] = rnd(commit)
        if onorder:
            rec["onorder"] = rnd(onorder)
        if cover is not None:
            rec["cover"] = rnd(cover, 1)
        if vs_normal is not None:
            rec["vs_normal_pct"] = rnd(vs_normal, 1)
        elif months_with_stock:
            # Stock exists but the 6-month baseline does not: either the item is
            # genuinely new, or it sat empty for most of the window and has just
            # come back. Both mean the same thing for the operator — there is no
            # normal to judge it against — so say that rather than invent a
            # percentage. Deliberately not called "new": several of these are old
            # items returning (e.g. a raw oil restocked after months at zero).
            rec["nobase"] = 1
        out_items.append(rec)

    out_items.sort(key=lambda r: (-r["value"], r["code"]))
    godowns = [{"co": key, "code": wc, "name": whs_meta.get(wc, ""),
                "class": classify(wc, whs_meta.get(wc, "")),
                "value": rnd(g["value"], 0), "items": g["items"]}
               for wc, g in sorted(god.items(), key=lambda kv: -kv[1]["value"])]

    company = {"key": key, "label": label, "schema": schema,
               "total_value": rnd(total_value, 0),
               "physical_value": rnd(physical_value, 0),
               # value on items omitted from the list (no stock, no movement —
               # pure cost-pool residue). total_value - sum(listed item value).
               "unlisted_value": rnd(total_value - listed_value, 0),
               "total_items": len(out_items),
               # approximate goods weight + share of goods value it covers
               "tonnes": rnd(tonnes, 1),
               "t_coverage_pct": rnd(100.0 * cov_num / cov_den, 0) if cov_den > 0 else 0,
               "status_counts": status_counts}
    return company, godowns, out_items


def main():
    connect()
    companies, godowns, items = [], [], []
    expiry = {}
    for key, label, schema in COMPANIES:
        print("company: %s" % label)
        try:
            c, g, it = build_company(key, label, schema)
            expiry[key] = build_expiry(key)
        except Exception as e:
            sys.exit("FATAL: extraction failed for %s: %s" % (key, e))
        companies.append(c); godowns.extend(g); items.extend(it)

    # ---- sanity guard: never overwrite good data with a broken refresh
    for c in companies:
        if c["total_value"] <= 0:
            sys.exit("REFUSED: %s total_value is %s — refresh looks broken, "
                     "keeping existing data.json." % (c["key"], c["total_value"]))
    if os.path.exists(OUT_PATH):
        try:
            with open(OUT_PATH) as f:
                prev = json.load(f)
            prev_counts = {c["key"]: c.get("total_items", 0)
                           for c in prev.get("companies", [])}
        except Exception:
            prev_counts = {}
        for c in companies:
            old = prev_counts.get(c["key"], 0)
            if old > 0 and c["total_items"] < 0.4 * old:
                sys.exit("REFUSED: %s item count fell %d -> %d (>60%% drop) — "
                         "refresh looks broken, keeping existing data.json."
                         % (c["key"], old, c["total_items"]))

    sites = build_sites(godowns, items)
    data = {"as_of": datetime.now().astimezone().isoformat(timespec="seconds"),
            "companies": companies, "godowns": godowns, "sites": sites,
            "expiry": expiry, "items": items}
    os.makedirs(SITE_DIR, exist_ok=True)
    blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    with open(OUT_PATH, "w") as f:
        f.write(blob)

    print("\n== run summary ==")
    for c in companies:
        sc = " ".join("%s=%d" % kv for kv in sorted(c["status_counts"].items()))
        print("%-5s items=%-5d value=%15s  physical=%15s  tonnes=%9s (cov %d%%)  [%s]"
              % (c["key"], c["total_items"], format(c["total_value"], ",.0f"),
                 format(c["physical_value"], ",.0f"),
                 format(c["tonnes"], ",.1f"), c["t_coverage_pct"], sc))
    for s in sites:
        print("site %-11s codes=%-3d value=%15s  goods=%15s  fa=%12s  items=%-4d tonnes=%9s (cov %d%%)"
              % (s["name"], len(s["codes"]), format(s["value"], ",.0f"),
                 format(s["goods_value"], ",.0f"),
                 format(s["fa_value"], ",.0f"), s["items"],
                 format(s["tonnes"], ",.1f"), s["t_coverage_pct"]))
    for k in sorted(expiry):
        e = expiry[k]
        if e.get("tracked"):
            # Units may differ per batch, so print the split rather than a sum
            # (beverages mixes GMS/MLS/PCS/LTR/KGS/UNT — see build_expiry).
            def _fmt(by):
                return " + ".join("%s %s" % (format(v, ",.0f"), u)
                                  for u, v in by.items()) or "0"
            print("expiry %-5s items=%-3d expired=%s  expiring90=%s"
                  % (k, e.get("expired_items", 0),
                     _fmt(e.get("expired_by_uom", {})),
                     _fmt(e.get("expiring90_by_uom", {}))))
        else:
            print("expiry %-5s not tracked (no batch carries an ExpDate)" % k)
    print("wrote %s (%.1f KB)" % (OUT_PATH, len(blob) / 1024))


if __name__ == "__main__":
    main()
