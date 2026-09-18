#!/usr/bin/env python3
"""tds.py — TDS on JIVO A/P bills from transporters and on goods (RM/PM). Rules: tds_rules.json.

  python tds.py apply <payload.json> --company OIL|MART|BEV [--out FILE] [--json]   (before sapb1 draft)
  python tds.py check <DocEntry> --company OIL|MART|BEV [--json]                   (after sapb1 draft)

Exit: 0 ok/PASS · 1 usage · 2 STOP (cannot decide safely) · 3 MISMATCH. Read-only: SELECTs through hana-sql.
"""
import argparse, csv, datetime as dt, io, json, os, re, shutil, subprocess, sys
from decimal import ROUND_HALF_UP, Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
RULES_FILE = os.path.join(HERE, "tds_rules.json")
BOOKS = {"OIL": ("JIVO_OIL_HANADB", "Oil"), "BEV": ("JIVO_BEVERAGES_HANADB", "Bev"), "MART": ("JIVO_MART_HANADB", "Mart")}
OK, USAGE, STOP, MISMATCH = 0, 1, 2, 3
SAFE, PAN_SHAPE, ZERO = re.compile(r"^[A-Za-z0-9_-]+$"), re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$"), Decimal(0)
NOT_APPLIED = "MISMATCH — TDS was calculated but not applied — open the draft in SAP B1 and save it once"


class Stop(Exception):
    """Cannot decide safely — exit 2. The message says what is wrong and who fixes it."""


class Usage(Exception):
    """Called wrongly — exit 1."""


def dec(v):
    return ZERO if v in (None, "") else Decimal(str(v))


def rupee(d):
    return int(d.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def pct(d):
    return "%s%%" % format(d.normalize(), "f")


def inr(v):
    """Indian grouping: 11340512 -> ₹1,13,40,512."""
    n = rupee(dec(v))
    s = str(abs(n))
    if len(s) > 3:
        head, pairs = s[:-3], []
        while len(head) > 2:
            pairs, head = [head[-2:]] + pairs, head[:-2]
        s = ",".join([head] + pairs) + "," + s[-3:]
    return ("-" if n < 0 else "") + "₹" + s


def safe(v, what):
    if not SAFE.match(str(v or "").strip()):
        raise Stop("%s %r has characters that cannot go into a SAP query — fix the input" % (what, v))
    return str(v).strip()


def hana_command():
    """Same resolution as ap-rm-pm/bin/jsap_route.py binary(): one build per OS in hana-sql/."""
    names = {"win32": ["hana-sql.exe", "hana-sql"], "darwin": ["hana-sql", "hana-sql.darwin"]}.get(sys.platform, ["hana-sql.linux", "hana-sql"])
    for path in (os.path.join(REPO, "hana-sql", n) for n in names):
        if os.path.exists(path):
            return [path]
    raise Stop("no hana-sql build for %s in %s — SAP cannot be read. Tell Daman." % (sys.platform, REPO))


def hana_query(name, sql, params):
    """The real query function; tests inject one with the same signature. hana-sql prints SQL NULL as NULL."""
    try:
        p = subprocess.run(hana_command() + ["-csv", sql], cwd=REPO, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Stop("SAP HANA unreachable (%s) — TDS cannot be decided. Try again; tell Daman if it persists." % exc)
    out = (p.stdout or "").strip()
    if p.returncode != 0 or out.startswith("QUERY ERROR"):
        text = (out if out.startswith("QUERY ERROR") else (p.stderr or out)).strip() or "exit %d" % p.returncode
        raise Stop("SAP HANA read failed (%s) — TDS cannot be decided. Try again; tell Daman if it persists." % text.splitlines()[0][:300])
    return [{k: (None if v == "NULL" else v) for k, v in r.items()} for r in csv.DictReader(io.StringIO(out))] if out else []


class Sap:
    """Every SAP read, each with a name the test fake answers by."""

    def __init__(self, query):
        self.q = query

    def card(self, s, code):
        code = safe(code, "CardCode")
        rows = self.q("card", 'SELECT c."CardCode", c."CardName", c."CardType", c."WTLiable", c."Currency", g."GroupName" '
                      'FROM "{s}"."OCRD" c LEFT JOIN "{s}"."OCRG" g ON g."GroupCode" = c."GroupCode" WHERE c."CardCode" = \'{c}\''
                      .format(s=s, c=code), dict(schema=s, code=code))
        return rows[0] if rows else None

    def tax_ids(self, s, code):
        return self.q("tax_ids", 'SELECT \'PAN\' "Src", "TaxId0" "Val" FROM "{s}"."CRD7" WHERE "CardCode" = \'{c}\' UNION ALL '
                      'SELECT \'GSTIN\' "Src", "GSTRegnNo" "Val" FROM "{s}"."CRD1" WHERE "CardCode" = \'{c}\''.format(s=s, c=code),
                      dict(schema=s, code=code))

    def card_codes(self, s, code):
        sql = 'SELECT "WTCode" FROM "{s}"."CRD4" WHERE "CardCode" = \'{c}\''.format(s=s, c=code)
        return [r["WTCode"] for r in self.q("card_codes", sql, dict(schema=s, code=code))]

    def owht(self, s):
        sql = 'SELECT "WTCode", "Rate" FROM "{s}"."OWHT" WHERE "Inactive" = \'N\''.format(s=s)
        return {r["WTCode"]: dec(r["Rate"]) for r in self.q("owht", sql, dict(schema=s))}

    def cards_on_pan(self, s, pan):
        sql = ('SELECT "CardCode" FROM "{s}"."OCRD" WHERE "CardType" = \'S\' AND ("CardCode" IN (SELECT "CardCode" FROM "{s}"."CRD7" '
               'WHERE UPPER(TRIM("TaxId0")) = \'{p}\') OR "CardCode" IN (SELECT "CardCode" FROM "{s}"."CRD1" WHERE '
               'LENGTH(TRIM("GSTRegnNo")) = 15 AND UPPER(SUBSTRING(TRIM("GSTRegnNo"), 3, 10)) = \'{p}\'))').format(s=s, p=safe(pan, "PAN"))
        return [r["CardCode"] for r in self.q("cards_on_pan", sql, dict(schema=s, pan=pan))]

    def yearly(self, s, cards, fy0, fy1, draft):
        """Posted A/P invoices minus posted A/P credit notes, before GST, plus A/P invoice drafts already in approval
        (WddStatus W/Y) — so bills entered together cannot each slip under ₹50 lakh. A draft never counts itself;
        when checking a draft, only drafts made before it count (so two drafts never count each other)."""
        part = ('SELECT \'{k}\' "Kind", COALESCE(SUM(d."DocTotal" - d."VatSum" + d."WTSum"), 0) "Amount" FROM "{s}"."{t}" d WHERE '
                'd."CardCode" IN ({c}) AND d."CANCELED" = \'N\' AND d."DocDate" BETWEEN \'{a}\' AND \'{b}\'{x}')
        args = dict(s=s, c=",".join("'%s'" % safe(c, "CardCode") for c in cards), a=fy0, b=fy1,
                    x=' AND (d."draftKey" IS NULL OR d."draftKey" <> %d)' % draft if draft else "")
        pending = dict(args, x=' AND d."ObjType" = \'18\' AND d."DocStatus" = \'O\' AND d."WddStatus" IN (\'W\', \'Y\')' +
                       (' AND d."DocEntry" < %d' % draft if draft else ""))
        # Divjot 17 Sept: last year's invoices stay out of this year — so a credit note against one (by base line, or by
        # carrying that invoice's number) does not lower this year's total.
        old = dict(args, x=(' AND NOT EXISTS (SELECT 1 FROM "{s}"."OPCH" o WHERE o."CardCode" = d."CardCode" AND o."CANCELED" = \'N\' '
                            'AND o."DocDate" < \'{a}\' AND o."NumAtCard" <> \'\' AND o."NumAtCard" = RTRIM(d."NumAtCard", \'.\')) '
                            'AND NOT EXISTS (SELECT 1 FROM "{s}"."RPC1" l JOIN "{s}"."OPCH" o ON o."DocEntry" = l."BaseEntry" '
                            'WHERE l."DocEntry" = d."DocEntry" AND l."BaseType" = 18 AND o."DocDate" < \'{a}\')').format(s=s, a=fy0))
        rows = self.q("yearly", part.format(k="INV", t="OPCH", **args) + " UNION ALL " + part.format(k="CN", t="ORPC", **old)
                      + " UNION ALL " + part.format(k="DRAFT", t="ODRF", **pending),
                      dict(schema=s, cards=sorted(cards), fy0=fy0, fy1=fy1, draft=draft))
        return sum((dec(r["Amount"]) * (-1 if r["Kind"] == "CN" else 1) for r in rows), ZERO)

    def grpo_lines(self, s, entries):
        sql = 'SELECT "DocEntry", "LineNum", "Quantity", "LineTotal" FROM "{s}"."PDN1" WHERE "DocEntry" IN ({e})'.format(
            s=s, e=",".join(str(int(e)) for e in entries))
        return {(int(r["DocEntry"]), int(r["LineNum"])): r for r in self.q("grpo_lines", sql, dict(schema=s, entries=sorted(entries)))}

    def draft(self, s, e):
        head = self.q("draft_header", 'SELECT "ObjType", "DocType", "CardCode", "CardName", "DocDate", "DocCur", "WTSum" '
                      'FROM "{s}"."ODRF" WHERE "DocEntry" = {e}'.format(s=s, e=e), dict(schema=s, entry=e))
        if not head:
            return None, [], []
        lines = self.q("draft_lines", 'SELECT "LineTotal", "WtLiable" FROM "{s}"."DRF1" WHERE "DocEntry" = {e} ORDER BY "LineNum"'
                       .format(s=s, e=e), dict(schema=s, entry=e))
        wt = self.q("draft_wt", 'SELECT "WTCode", "TaxbleAmnt", "WTAmnt" FROM "{s}"."DRF5" WHERE "AbsEntry" = {e}'.format(s=s, e=e),
                    dict(schema=s, entry=e))
        return head[0], lines, wt


def line_amounts(sap, schema, lines):
    """LineTotal, else Quantity x UnitPrice less DiscountPercent, else pro-rated from the GRPO line (BaseType 20)."""
    def from_grpo(ln):
        return ln.get("LineTotal") is None and None in (ln.get("Quantity"), ln.get("UnitPrice")) and str(ln.get("BaseType")) == "20" \
            and ln.get("BaseEntry") is not None and ln.get("BaseLine") is not None
    need = sorted({int(ln["BaseEntry"]) for ln in lines if from_grpo(ln)})
    grpo, out = sap.grpo_lines(schema, need) if need else {}, []
    for n, ln in enumerate(lines, 1):
        row = grpo.get((int(ln["BaseEntry"]), int(ln["BaseLine"]))) if from_grpo(ln) else None
        if ln.get("LineTotal") is not None:
            out.append(dec(ln["LineTotal"]))
        elif ln.get("Quantity") is not None and ln.get("UnitPrice") is not None:
            out.append(dec(ln["Quantity"]) * dec(ln["UnitPrice"]) * (1 - dec(ln.get("DiscountPercent")) / 100))
        elif row is None:
            raise Stop("line %d has no LineTotal, no Quantity x UnitPrice and no GRPO line to price it from — fix the payload" % n)
        elif ln.get("Quantity") is not None and dec(row["Quantity"]) > 0:
            out.append(dec(row["LineTotal"]) * dec(ln["Quantity"]) / dec(row["Quantity"]))
        else:
            out.append(dec(row["LineTotal"]))
    return out


def find_pan(sap, schema, code):
    """CRD7.TaxId0, else characters 3-12 of the 15-character GSTIN."""
    rows = sap.tax_ids(schema, code)
    for src, cut in (("PAN", lambda v: v), ("GSTIN", lambda v: v[2:12] if len(v) == 15 else "")):
        pans = {p for p in (cut((r["Val"] or "").strip().upper()) for r in rows if r["Src"] == src) if PAN_SHAPE.match(p)}
        if len(pans) > 1:
            raise Stop("vendor card %s carries more than one PAN (%s) — whoever keeps vendor masters fixes the card" % (code, ", ".join(sorted(pans))))
        if pans:
            return pans.pop()
    return None


def pick_code(sap, schema, book, card, rule):
    """The card's code for this rule if it has one, else the default. The rate always comes from SAP's OWHT."""
    owht, on_card = sap.owht(schema), sap.card_codes(schema, card["CardCode"])
    code = next((c for c in rule["codes_taken_from_vendor_card"] if c in on_card and c in owht), rule["default_code"])
    if code not in owht or owht[code] != dec(rule["rate_percent"]):
        raise Stop("%s's OWHT has code %s at %s but tds_rules.json says %s%% — tell Divjot before this bill goes out"
                   % (BOOKS[book][1], code, pct(owht[code]) if code in owht else "no active rate", rule["rate_percent"]))
    return code, owht[code], "" if code in on_card else ", not on the vendor card"


def yearly_total(rules, sap, book, card, pan, date, draft):
    y = date.year if date.month >= 4 else date.year - 1
    total, counted, notes = ZERO, [], []
    for b in rules["deductor_groups"][book]:
        if pan:
            cards = set(sap.cards_on_pan(BOOKS[b][0], pan)) | ({card["CardCode"]} if b == book else set())
        elif b == book:
            cards = {card["CardCode"]}
        else:  # no PAN: same CardCode in the other book — but only if it is the same party there
            other = sap.card(BOOKS[b][0], card["CardCode"])
            same = bool(other) and re.sub(r"\W", "", other["CardName"].upper()) == re.sub(r"\W", "", card["CardName"].upper())
            cards = {card["CardCode"]} if same else set()
            if other and not same:
                notes.append("%s in %s is %s — a different party, not counted" % (card["CardCode"], BOOKS[b][1], other["CardName"]))
        if cards:
            total += sap.yearly(BOOKS[b][0], sorted(cards), "%d-04-01" % y, date.isoformat(), draft if b == book else None)
        counted.append("%s %s" % (BOOKS[b][1], ", ".join(sorted(cards)) or "none"))
    return total, counted, notes + ([] if pan else ["no PAN on the card — counted by vendor code only"])


def decide(rules, sap, book, doc, draft=None):
    """-> {kind: transport | goods | untouched, rows, summary, notes}."""
    if doc["credit"]:
        return {"kind": "untouched", "label": "credit note", "rows": [], "summary": [], "notes": []}
    schema, t, g = BOOKS[book][0], rules["transport"], rules["goods"]
    card = sap.card(schema, doc["card"])
    if not card or card["CardType"] != "S":
        raise Stop("%s is not a vendor card in %s — check the CardCode and --company" % (doc["card"], BOOKS[book][1]))
    transporter = card["GroupName"] == t["vendor_group_name"]
    try:
        pan = find_pan(sap, schema, card["CardCode"])
    except Stop:  # a messy card only matters when TDS is ours to decide
        if doc["service"] and not transporter and card["CardCode"] not in t["declaration_received_card_codes"]:
            return {"kind": "untouched", "label": "service bill", "rows": [], "summary": [], "notes": []}
        raise
    exempt = t["declaration_received_pans"].get(pan) or t["declaration_received_card_codes"].get(card["CardCode"])
    if doc["service"] and not (exempt or transporter):
        return {"kind": "untouched", "label": "service bill", "rows": [], "summary": [], "notes": []}
    d = {"kind": "transport" if exempt or transporter else "goods", "rows": [], "summary": [], "notes": [], "pan": pan}
    if exempt:
        d["summary"].append("Transporter · declaration received (%s) · no TDS" % exempt)
        return d
    if (doc["currency"] or card["Currency"]) not in (None, "INR", "##"):
        raise Stop("this bill is in %s — the rules cover rupee bills only; Divjot decides it" % (doc["currency"] or card["Currency"]))
    if not transporter and card["GroupName"] in g["no_tds_vendor_groups"]:
        d["summary"].append("Goods · vendor group %s · no TDS" % card["GroupName"])
        return d
    bill = sum(line_amounts(sap, schema, doc["lines"]), ZERO)
    if transporter:
        code, rate, src = pick_code(sap, schema, book, card, t)
        taxable, text = bill, "Transporter · no declaration on file · TDS {r} on the whole bill {x} = {w} (code {c}{s})"
    else:
        before, counted, d["notes"] = yearly_total(rules, sap, book, card, pan, doc["date"], draft)
        limit = dec(g["threshold_per_year"])
        lakh = "₹%s lakh" % format((limit / 100000).normalize(), "f")
        taxable = max(ZERO, min(bill, before + bill - limit))
        head = "Goods (RM/PM) · %s this year %s before this bill" % ("+".join(BOOKS[b][1] for b in rules["deductor_groups"][book]), inr(before))
        d["summary"].append("yearly total counts " + " · ".join(counted))
        if taxable <= 0:
            d["summary"].append("%s + this bill %s = %s → under %s · no TDS" % (head, inr(bill), inr(before + bill), lakh))
            return d
        code, rate, src = pick_code(sap, schema, book, card, g)
        text = head + (" → over %s · TDS {r} on {x} = {w} (code {c}{s})" % lakh if before >= limit else
                       " + this bill %s → crosses %s · TDS {r} on the {x} above it = {w} (code {c}{s})" % (inr(bill), lakh))
    taxable = taxable.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    wt = rupee(rate * taxable / 100)
    if wt > 0 and card["WTLiable"] != "Y":
        raise Stop("TDS of %s (code %s) is due but vendor card %s is not marked TDS-liable in %s, so SAP will not deduct it — "
                   "whoever keeps vendor masters ticks it on the card, then run again" % (inr(wt), code, card["CardCode"], BOOKS[book][1]))
    d["rows"] = [{"WTCode": code, "TaxableAmount": float(taxable), "WTAmount": wt}]
    d["summary"].append(text.format(r=pct(rate), x=inr(taxable), w=inr(wt), c=code, s=src))
    return d


def book_of(company):
    for key, (schema, _) in BOOKS.items():
        if str(company).strip().upper() in (key, schema):
            return key
    raise Usage("--company must be OIL, MART, BEV or a full schema name, not %r" % company)


def show(args, head, d, extra):
    if args.json:
        return print(json.dumps(dict(d, **extra), indent=2, ensure_ascii=False))
    print("\n".join([head] + ["  " + s for s in d["summary"]] + ["  note: " + s for s in d["notes"]] + [extra["message"]]))


def cmd_apply(args, rules, sap):
    book = book_of(args.company)
    try:
        with open(args.payload, encoding="utf-8-sig") as fh:
            p = json.load(fh)
    except OSError as exc:
        raise Usage("cannot read %s: %s" % (args.payload, exc))
    except ValueError as exc:
        raise Stop("%s is not valid JSON: %s" % (args.payload, exc))
    if not isinstance(p, dict):
        raise Stop("%s is not a draft payload" % args.payload)
    lines = p.get("DocumentLines")
    if not p.get("CardCode") or not lines or not isinstance(lines, list) or not all(isinstance(x, dict) for x in lines):
        raise Stop("the payload needs a CardCode and DocumentLines")
    obj = str(p.get("DocObjectCode") or "").lower()
    if not obj:  # entry skills send it with `sapb1 draft purchase-invoice`, which adds DocObjectCode itself
        if any(str(x.get("BaseType")) in ("18", "19") for x in lines):
            raise Stop('lines are copied from an A/P invoice, so this looks like a credit note — add "DocObjectCode" to the payload')
        obj = "opurchaseinvoices"
    if obj not in ("opurchaseinvoices", "18", "opurchasecreditnotes", "19"):
        raise Stop('DocObjectCode %r is not an A/P invoice or A/P credit note' % p.get("DocObjectCode"))
    try:
        date = dt.date.fromisoformat(str(p["DocDate"])[:10]) if p.get("DocDate") else dt.date.today()
    except ValueError:
        raise Stop("DocDate %r is not a date" % p["DocDate"])
    d = decide(rules, sap, book, {"credit": obj in ("opurchasecreditnotes", "19"), "service": p.get("DocType") == "dDocument_Service",
                                  "card": p["CardCode"], "date": date, "currency": p.get("DocCurrency"), "lines": lines})
    out = args.out or args.payload
    if d["kind"] == "untouched":  # service bills and credit notes: not ours to change
        if os.path.abspath(out) != os.path.abspath(args.payload):
            shutil.copyfile(args.payload, out)
        message = "%s — TDS left as the skill set it" % d["label"]
    else:
        for ln in lines:
            ln["WTLiable"] = "tYES" if d["rows"] else "tNO"
        p.pop("WithholdingTaxDataCollection", None)
        if d["rows"]:
            p["WithholdingTaxDataCollection"] = d["rows"]
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(p, indent=2, ensure_ascii=False) + "\n")
        wt = sum(r["WTAmount"] for r in d["rows"])
        message = ("TDS on this bill: %s" % inr(wt) if wt else "No TDS on this bill") + " · wrote " + out
    show(args, "%s · %s · %s" % (p["CardCode"], BOOKS[book][1], date), d, {"result": "OK", "message": message, "written_to": out})
    return OK


def cmd_check(args, rules, sap):
    if not str(args.docentry).isdigit() or int(args.docentry) <= 0:
        raise Usage("DocEntry must be a positive whole number, not %r" % args.docentry)
    entry, book = int(args.docentry), book_of(args.company)
    head, lines, wt = sap.draft(BOOKS[book][0], entry)
    if head is None or str(head["ObjType"]) not in ("18", "19"):
        raise Stop("draft %d in %s is %s — DocEntry numbers differ per book; check --company" % (entry, BOOKS[book][1], "not there"
                   if head is None else "object type %s, not an A/P invoice or credit note" % head["ObjType"]))
    d = decide(rules, sap, book, {"credit": str(head["ObjType"]) == "19", "service": head["DocType"] == "S", "card": head["CardCode"],
                                  "date": dt.date.fromisoformat(head["DocDate"][:10]), "currency": head["DocCur"],
                                  "lines": [{"LineTotal": ln["LineTotal"]} for ln in lines]}, draft=entry)
    wt_sum, in_sap = dec(head["WTSum"]), {}
    for r in wt:
        in_sap[r["WTCode"]] = in_sap.get(r["WTCode"], ZERO) + dec(r["WTAmnt"])
    not_applied = (any(ln["WtLiable"] == "Y" for ln in lines) or bool(wt)) and abs(wt_sum) < Decimal("0.5")
    expected = {r["WTCode"]: dec(r["WTAmount"]) for r in d["rows"]}
    total = sum(expected.values(), ZERO)
    off = [c for c in set(expected) | set(in_sap) if abs(expected.get(c, ZERO) - in_sap.get(c, ZERO)) > 1]
    if d["kind"] == "untouched":
        result, message = ("MISMATCH", NOT_APPLIED) if not_applied else ("PASS", "PASS — %s, not recalculated" % d["label"])
    elif not off and abs(wt_sum - total) <= 1:
        result, message = "PASS", "PASS — TDS matches the rules (%s)" % inr(total)
    elif total > 0 and not_applied:
        result, message = "MISMATCH", NOT_APPLIED
    else:
        result, message = "MISMATCH", "MISMATCH — the rules say %s TDS (%s), the draft deducts %s. Whoever made the draft sets " \
            "Withholding Tax on it in SAP B1, then runs check again." % (inr(total), "; ".join("code %s %s on %s" % (
                r["WTCode"], inr(r["WTAmount"]), inr(r["TaxableAmount"])) for r in d["rows"]) or "none", inr(wt_sum))
    if d["kind"] != "untouched":
        d["summary"].append("rules: %s · SAP draft: %s, WTSum %s" % (", ".join("%s %s" % (c, inr(v)) for c, v in expected.items()) or
                            "no TDS", ", ".join("%s %s" % (c, inr(v)) for c, v in in_sap.items()) or "no TDS rows", inr(wt_sum)))
    show(args, "Draft %d · %s · %s %s · %s" % (entry, BOOKS[book][1], head["CardCode"], head["CardName"], head["DocDate"][:10]), d,
         {"result": result, "message": message, "draft": entry, "sap": {c: float(v) for c, v in in_sap.items()}, "wt_sum": float(wt_sum)})
    return OK if result == "PASS" else MISMATCH


def main(argv=None, query=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="tds.py", description="TDS on JIVO A/P bills: transport and goods.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name, target in (("apply", "payload"), ("check", "docentry")):
        cmd = sub.add_parser(name)
        cmd.add_argument(target)
        cmd.add_argument("--company", required=True)
        cmd.add_argument("--json", action="store_true")
    sub.choices["apply"].add_argument("--out")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse exits 2, which here would read as STOP
        return OK if exc.code in (0, None) else USAGE
    try:
        try:
            with open(RULES_FILE, encoding="utf-8") as fh:
                rules = json.load(fh)
        except (OSError, ValueError) as exc:
            raise Stop("tds_rules.json cannot be read (%s) — tell Daman" % exc)
        sap = Sap(query or hana_query)
        return cmd_apply(args, rules, sap) if args.cmd == "apply" else cmd_check(args, rules, sap)
    except (Usage, Stop, Exception) as exc:  # anything unexpected is a STOP, never "typed wrong"
        code, word = (USAGE, "USAGE") if isinstance(exc, Usage) else (STOP, "STOP")
        if not isinstance(exc, (Usage, Stop)):
            exc = Stop("unexpected %s: %s — nothing was decided; tell Daman" % (type(exc).__name__, exc))
        print(json.dumps({"result": word, "message": str(exc)}, ensure_ascii=False) if args.json else "%s — %s" % (word, exc))
        return code


if __name__ == "__main__":
    sys.exit(main())
