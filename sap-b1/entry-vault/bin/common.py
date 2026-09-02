"""Shared HANA access for the entry-vault miners.

Everything goes through the read-only `hana-sql` binary — no second SQL path,
no driver, no credentials in this file. The guard in hana-sql is the only
thing standing between a miner and the live books, so we do not go around it.
"""
from __future__ import annotations
import csv, io, os, subprocess, sys, time, functools

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
HANA = os.path.join(ROOT, "hana-sql", "hana-sql")
ENV_CANDIDATES = [
    os.environ.get("HANA_ENV", ""),
    # the Mac and the fleet boxes reach HANA by different routes; try both so the
    # same miner script runs unmodified wherever it lands
    os.path.join(ROOT, "connections", "hana-office-bridge.env"),
    os.path.join(ROOT, "connections", "hana-vps-direct.env"),
    os.path.join(ROOT, "connections", "hana.env"),
]
COMPANIES = {"OIL": "JIVO_OIL_HANADB", "MART": "JIVO_MART_HANADB", "BEV": "JIVO_BEVERAGES_HANADB"}


def _env() -> str:
    for c in ENV_CANDIDATES:
        if c and os.path.exists(c):
            return c
    raise SystemExit("no HANA env file found (tried connections/hana-office-bridge.env)")


BRIDGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bridge.sh")
# A dropped SSH tunnel looks exactly like this, and over a multi-hour mining run it
# will happen. Repair once and retry rather than failing a whole note's worth of work.
TRANSIENT = ("connection refused", "i/o timeout", "connection reset",
             "broken pipe", "no route to host", "eof", "closed by remote")


def q(sql: str, timeout: int = 600, tries: int = 4) -> list[dict]:
    """Run one read-only SELECT and return rows as dicts, repairing the tunnel if it drops."""
    last = ""
    for attempt in range(tries):
        p = subprocess.run([HANA, "-env", _env(), "-csv", sql],
                           capture_output=True, text=True, timeout=timeout)
        if p.returncode == 0:
            return list(csv.DictReader(io.StringIO(p.stdout)))
        last = (p.stderr.strip() or p.stdout.strip())[:600]
        low = last.lower()
        if attempt + 1 < tries and any(t in low for t in TRANSIENT):
            subprocess.run(["bash", BRIDGE, "-q"], capture_output=True, text=True, timeout=180)
            time.sleep(2 + 3 * attempt)
            continue
        break
    raise RuntimeError(f"hana-sql failed: {last}\nSQL: {sql[:400]}")


def q1(sql: str, timeout: int = 600):
    """Run a SELECT expected to return a single value."""
    r = q(sql, timeout)
    if not r:
        return None
    return list(r[0].values())[0]


@functools.lru_cache(maxsize=None)
def columns(schema: str, table: str) -> tuple:
    """(name, data_type, length, position) for every column, in table order."""
    rows = q(f"""SELECT "COLUMN_NAME","DATA_TYPE_NAME","LENGTH","POSITION"
                 FROM SYS.TABLE_COLUMNS
                 WHERE "SCHEMA_NAME"='{schema}' AND "TABLE_NAME"='{table}'
                 ORDER BY "POSITION" """)
    return tuple((r["COLUMN_NAME"], r["DATA_TYPE_NAME"], r["LENGTH"], int(r["POSITION"])) for r in rows)


def table_exists(schema: str, table: str) -> bool:
    return bool(q1(f"""SELECT COUNT(*) FROM SYS.TABLES WHERE "SCHEMA_NAME"='{schema}' AND "TABLE_NAME"='{table}'"""))


NUMERIC = {"INTEGER", "BIGINT", "SMALLINT", "TINYINT", "DECIMAL", "DOUBLE", "REAL", "SMALLDECIMAL"}
TEXTUAL = {"NVARCHAR", "VARCHAR", "CHAR", "NCHAR", "SHORTTEXT", "ALPHANUM"}
TEMPORAL = {"DATE", "TIMESTAMP", "SECONDDATE", "TIME", "LONGDATE"}
# HANA refuses COUNT(DISTINCT) and most aggregates on LOBs, so they are probed by
# length only and never counted.
LOB = {"CLOB", "NCLOB", "BLOB", "TEXT", "BINTEXT", "ST_GEOMETRY", "ST_POINT"}


def filled_expr(col: str, dtype: str) -> str:
    """SQL that is 1 when the operator actually put something in this field.

    'Filled' is deliberately stricter than 'not null': SAP writes '' into unused
    text fields and 0 into unused numerics, so a NULL test alone reports a field
    as 100% populated when in truth nobody ever types in it.
    """
    c = f'"{col}"'
    if dtype in TEXTUAL:
        return f"SUM(CASE WHEN {c} IS NOT NULL AND TRIM({c}) <> '' THEN 1 ELSE 0 END)"
    if dtype in NUMERIC:
        return f"SUM(CASE WHEN {c} IS NOT NULL AND {c} <> 0 THEN 1 ELSE 0 END)"
    if dtype in LOB:
        return f"SUM(CASE WHEN {c} IS NOT NULL AND LENGTH({c}) > 0 THEN 1 ELSE 0 END)"
    return f"SUM(CASE WHEN {c} IS NOT NULL THEN 1 ELSE 0 END)"


# Header table -> (line tables, ObjType, plain-English name). ObjType is what SAP
# stamps on drafts, approval requests and journal entries, so it is the join key
# between "the document" and "everything that happened to it".
DOCS = {
    "OINV": (["INV1", "INV12", "INV3"],  13, "A/R Invoice"),
    "ORIN": (["RIN1", "RIN12", "RIN3"],  14, "A/R Credit Memo"),
    "ODLN": (["DLN1", "DLN12"],          15, "Delivery"),
    "ORDN": (["RDN1", "RDN12"],          16, "A/R Return"),
    "ORDR": (["RDR1", "RDR12"],          17, "Sales Order"),
    "OPCH": (["PCH1", "PCH12", "PCH3"],  18, "A/P Invoice"),
    "ORPC": (["RPC1", "RPC12", "RPC3"],  19, "A/P Credit Memo"),
    "OPDN": (["PDN1", "PDN12"],          20, "Goods Receipt PO (GRPO)"),
    "ORPD": (["RPD1", "RPD12"],          21, "Goods Return"),
    "OPOR": (["POR1", "POR12"],          22, "Purchase Order"),
    "OQUT": (["QUT1", "QUT12"],          23, "Sales Quotation"),
    "ORCT": (["RCT2", "RCT1", "RCT3"],   24, "Incoming Payment"),
    "OVPM": (["VPM2", "VPM1", "VPM3", "VPM4"], 46, "Outgoing Payment"),
    "OJDT": (["JDT1"],                   30, "Journal Entry"),
    "OIGN": (["IGN1"],                   59, "Goods Receipt (inventory)"),
    "OIGE": (["IGE1"],                   60, "Goods Issue (inventory)"),
    "OWTR": (["WTR1"],                   67, "Stock Transfer"),
    "OIPF": (["IPF1", "IPF2", "IPF3"],   69, "Landed Costs"),
    "OMRV": (["MRV1"],                  162, "Inventory Revaluation"),
    "OWOR": (["WOR1"],                  202, "Production Order"),
    "OWTQ": (["WTQ1"],          1250000001, "Inventory Transfer Request"),
    "ORRR": (["RRR1"],          1250000025, "Return Request"),
    "ODRF": (["DRF1", "DRF12"],          -1, "Document Draft (any type)"),
    "OPDF": (["PDF1", "PDF2", "PDF3", "PDF4", "PDF8"], -1, "Payment Draft"),
    "OBTF": (["BTF1"],                   -1, "Journal Voucher (parked batch)"),
    "OBNK": (["BNK1"],                   -1, "Bank Statement"),
}
OBJTYPE_NAME = {v[1]: v[2] for v in DOCS.values() if v[1] > 0}
OBJTYPE_NAME.update({
    -3: "Opening balance / cutover", 321: "Internal reconciliation (period-end)",
    254000061: "India localisation object 254000061", 254000062: "India localisation object 254000062",
    1470000113: "Purchase Request", 234000031: "Inventory Counting",
    203: "A/R Down Payment", 204: "A/P Down Payment", 76: "Deposit", 57: "Check for Payment",
})
