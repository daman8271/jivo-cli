#!/usr/bin/env python3
"""summary_pdf.py - one PDF for everything the CLI wrote to SAP on a day.

Two steps, both read-only against SAP:

  collect  read the shared write logs for a date, read every touched draft
           back from SAP (all three companies), find its approval request and
           any invoice it posted as, pull each Claude session's final report
           from the transcripts on this machine, and write:
             DIR/entries.json   machine-readable facts
             DIR/skeleton.md    the report with every table already filled
             DIR/sessions.md    what each session said, for the warnings section
  render   markdown -> HTML -> PDF through the gstack browse daemon, then copy
           the PDF to ~/Downloads (or --pdf PATH).

Usage:
  summary_pdf.py collect [--date YYYY-MM-DD] [--out DIR] [--no-sap] [--no-transcripts]
  summary_pdf.py render DIR/report.md [--pdf /path/out.pdf] [--no-downloads]

Never writes to SAP. Only sapb1 query is called.
"""
import argparse
import datetime as dt
import glob
import html
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def repo_root():
    d = HERE
    for _ in range(8):
        if os.path.exists(os.path.join(d, "sap-b1", "cli", "sapb1")) or os.path.exists(
            os.path.join(d, "sap-b1", "cli", "sapb1.exe")
        ):
            return d
        d = os.path.dirname(d)
    return os.getcwd()


ROOT = repo_root()
CLI_DIR = os.path.join(ROOT, "sap-b1", "cli")
SAPB1 = os.path.join(CLI_DIR, "sapb1.exe" if os.name == "nt" else "sapb1")
BROWSE = os.path.expanduser("~/.claude/skills/gstack/browse/dist/browse")

CO_SHORT = {
    "JIVO_OIL_HANADB": "Oil",
    "JIVO_MART_HANADB": "Mart",
    "JIVO_BEVERAGES_HANADB": "Bev",
}
POSTED_ENTITY = {
    "oPurchaseInvoices": "PurchaseInvoices",
    "oPurchaseDeliveryNotes": "PurchaseDeliveryNotes",
    "oPurchaseCreditNotes": "PurchaseCreditNotes",
    "oPurchaseOrders": "PurchaseOrders",
    "oInvoices": "Invoices",
    "oOrders": "Orders",
}


# ----------------------------------------------------------------- helpers
def inr(n):
    """Indian grouping: 1731060 -> ₹17,31,060 ; keeps paise only if non-zero."""
    if n is None:
        return ""
    neg = n < 0
    n = abs(n)
    whole = int(round(n))
    frac = round(n - int(n), 2)
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    if frac and abs(n - whole) > 0.005:
        s = s + ("%.2f" % frac)[1:]
    return ("-" if neg else "") + "₹" + s


def ddmmyyyy(iso):
    if not iso:
        return ""
    return iso[8:10] + "-" + iso[5:7] + "-" + iso[0:4]


def run_sapb1(args, timeout=120):
    """Run sapb1 from its own directory so it reads the .env there."""
    p = subprocess.run(
        [SAPB1] + args, cwd=CLI_DIR, capture_output=True, text=True, timeout=timeout
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip() or "sapb1 failed")
    out = p.stdout.strip()
    if not out:
        return []
    data = json.loads(out)
    if isinstance(data, dict):
        data = data.get("rows") or data.get("value") or []
    return data


def sap_query(entity, company, flt, extra=None):
    args = ["query", entity, "--company", company, "--filter", flt, "--json"]
    if extra:
        args += extra
    return run_sapb1(args)


# ---------------------------------------------------------------- write log
def read_write_logs(date):
    rows, seen = [], set()
    for f in sorted(glob.glob(os.path.join(ROOT, "queries", "*", "sap-writes.jsonl"))):
        with open(f, encoding="utf-8", errors="replace") as fh:
            for ln, line in enumerate(fh, 1):
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                t = str(d.get("time", ""))
                if not t.startswith(date):
                    continue
                key = (t, d.get("event"), d.get("method"), d.get("path"), d.get("company_db"))
                if key in seen:  # the same write is sometimes logged in two files
                    continue
                seen.add(key)
                d["_file"] = os.path.relpath(f, ROOT)
                d["_line"] = ln
                rows.append(d)
    rows.sort(key=lambda r: r.get("time", ""))
    return rows


def resolve_origin(origin):
    """A SaveDraftToDocument intent carries origin={file,line} of the creating
    outcome. Read that line and return its DocEntry."""
    try:
        path = os.path.join(ROOT, origin["file"])
        with open(path, encoding="utf-8", errors="replace") as fh:
            for ln, line in enumerate(fh, 1):
                if ln == origin["line"]:
                    d = json.loads(line)
                    m = re.search(r"DocEntry=(\d+)", str(d.get("result_key", "")))
                    return int(m.group(1)) if m else None
    except (OSError, ValueError, KeyError):
        return None
    return None


def digest_log(rows):
    docs = {}  # (company_db, DocEntry) -> dict
    errors, deletes, att_rows = [], [], {}  # att_rows: (company_db, row) -> {time,user}

    def doc(co, de):
        return docs.setdefault((co, de), {
            "company_db": co, "company": CO_SHORT.get(co, co), "doc_entry": de,
            "created_at": None, "created_by": None, "submitted_at": None,
            "submit_status": None, "patched": 0, "attachment_rows": [], "deleted": False,
        })

    for i, r in enumerate(rows):
        co, path, ev = r.get("company_db"), r.get("path", ""), r.get("event")
        m_id = re.match(r"(\w+)\((\d+)\)", path)
        if ev == "outcome" and r.get("method") == "POST" and path == "Drafts" and r.get("status") == 201:
            m = re.search(r"DocEntry=(\d+)", str(r.get("result_key", "")))
            if m:
                d = doc(co, int(m.group(1)))
                d["created_at"], d["created_by"] = r["time"], r.get("user")
        elif ev == "intent" and path == "DraftsService_SaveDraftToDocument":
            de = resolve_origin(r.get("origin") or {})
            if de is None:
                continue
            d = doc(co, de)
            d["submitted_at"] = r["time"]
            d["submitted_by"] = r.get("user")
            # the matching outcome is the next SaveDraftToDocument outcome in this company
            for r2 in rows[i + 1:i + 6]:
                if r2.get("event") == "outcome" and r2.get("path") == path and r2.get("company_db") == co:
                    d["submit_status"] = r2.get("status")
                    break
        elif ev == "outcome" and m_id and m_id.group(1) == "Drafts" and r.get("method") == "PATCH" and r.get("status") == 204:
            doc(co, int(m_id.group(2)))["patched"] += 1
        elif ev == "outcome" and m_id and m_id.group(1) == "Drafts" and r.get("method") == "DELETE" and r.get("status") == 204:
            d = doc(co, int(m_id.group(2)))
            d["deleted"], d["deleted_at"], d["deleted_by"] = True, r["time"], r.get("user")
            # a POST Drafts 201 by the same user in the same book within 3 minutes is almost always the rebuild
            t0 = dt.datetime.fromisoformat(r["time"])
            for r2 in rows[i + 1:i + 40]:
                if (r2.get("event") == "outcome" and r2.get("method") == "POST" and r2.get("path") == "Drafts"
                        and r2.get("status") == 201 and r2.get("company_db") == co and r2.get("user") == r.get("user")):
                    m2 = re.search(r"DocEntry=(\d+)", str(r2.get("result_key", "")))
                    if m2 and (dt.datetime.fromisoformat(r2["time"]) - t0).total_seconds() < 180:
                        d["rebuilt_as"] = int(m2.group(1))
                    break
            deletes.append({"company": CO_SHORT.get(co, co), "doc_entry": int(m_id.group(2)), "time": r["time"],
                            "user": r.get("user"), "rebuilt_as": d.get("rebuilt_as")})
        elif ev == "outcome" and m_id and m_id.group(1) == "Attachments2" and r.get("status") == 204:
            att_rows.setdefault((co, int(m_id.group(2))), {"time": r["time"], "user": r.get("user")})
        if ev == "outcome" and isinstance(r.get("status"), int) and r["status"] >= 400:
            errors.append({"time": r["time"], "user": r.get("user"), "company": CO_SHORT.get(co, co),
                           "method": r.get("method"), "path": path, "error": r.get("error")})
    return docs, errors, deletes, att_rows


# --------------------------------------------------------------- SAP readback
def fill_from_row(d, r):
    lines = r.get("DocumentLines") or []
    wt = r.get("WithholdingTaxDataCollection") or []
    grpos = sorted({l.get("BaseEntry") for l in lines if l.get("BaseEntry")})
    d.update({
        "doc_num": r.get("DocNum"), "object": r.get("DocObjectCode"),
        "card_code": r.get("CardCode"), "card_name": r.get("CardName"),
        "bill_no": r.get("NumAtCard"), "doc_date": r.get("DocDate"),
        "total": r.get("DocTotal"), "vat": r.get("VatSum"),
        "tds": sum((w.get("WTAmount") or 0) for w in wt),
        "tds_codes": sorted({w.get("WTCode") for w in wt if w.get("WTCode")}),
        "auth": r.get("AuthorizationStatus"), "status": r.get("DocumentStatus"),
        "series": r.get("Series"), "branch": r.get("BPLName") or r.get("BPL_IDAssignedToInvoice"),
        "attachment_row": r.get("AttachmentEntry"), "user_sign": r.get("UserSign"),
        "creation_date": r.get("CreationDate"),
        "lines": len(lines), "n_grpo": len(grpos), "base_entries": grpos,
        "comments": (r.get("Comments") or "").strip(),
    })


def readback(docs, att_rows=None):
    by_co = {}
    for (co, de) in docs:
        by_co.setdefault(co, []).append(de)
    for co, ids in by_co.items():
        for i in range(0, len(ids), 8):
            chunk = ids[i:i + 8]
            flt = " or ".join("DocEntry eq %d" % x for x in chunk)
            try:
                rows = sap_query("Drafts", co, flt)
            except Exception as e:  # keep going; the skeleton marks the gap
                for x in chunk:
                    docs[(co, x)]["sap_error"] = str(e)[:200]
                continue
            found = set()
            for r in rows:
                de = r.get("DocEntry")
                found.add(de)
                d = docs.get((co, de))
                if d is None:
                    continue
                fill_from_row(d, r)
            for x in chunk:
                if x not in found and "sap_error" not in docs[(co, x)]:
                    docs[(co, x)]["sap_error"] = "not in Drafts any more (posted, or deleted)"
    # drafts touched only through an attachment row today (a scan appended to an older draft)
    known_rows = {(co, d.get("attachment_row")) for (co, _), d in docs.items() if d.get("attachment_row")}
    orphan_rows = []
    for (co, row), meta in (att_rows or {}).items():
        if (co, row) in known_rows:
            continue
        try:
            rows = sap_query("Drafts", co, "AttachmentEntry eq %d" % row)
        except Exception:
            rows = []
        if not rows:
            orphan_rows.append({"company": CO_SHORT.get(co, co), "row": row, "time": meta["time"], "user": meta["user"]})
            continue
        r = rows[0]
        d = docs.setdefault((co, r["DocEntry"]), {
            "company_db": co, "company": CO_SHORT.get(co, co), "doc_entry": r["DocEntry"],
            "created_at": None, "created_by": None, "submitted_at": None, "submit_status": None,
            "patched": 0, "attachment_rows": [], "deleted": False})
        d["touched"] = "attachment row %d written at %s by %s" % (row, meta["time"][11:16], meta["user"])
        fill_from_row(d, r)
    # approval requests + posted documents
    for (co, de), d in list(docs.items()):
        if d.get("sap_error") and not d.get("deleted"):
            continue
        try:
            reqs = sap_query("ApprovalRequests", co, "DraftEntry eq %d" % de)
            if reqs:
                r = reqs[-1]
                lines = r.get("ApprovalRequestLines") or []
                d["approval"] = {"code": r.get("Code"), "template": r.get("ApprovalTemplatesID"),
                                 "status": (lines[0].get("Status") if lines else None),
                                 "time": r.get("CreationTime")}
        except Exception:
            pass
        ent = POSTED_ENTITY.get(d.get("object") or "")
        if ent and d.get("status") == "bost_Close" and d.get("bill_no") and d.get("card_code"):
            try:
                bill = str(d["bill_no"]).replace("'", "''")
                rows = sap_query(ent, co, "NumAtCard eq '%s' and CardCode eq '%s'" % (bill, d["card_code"]),
                                 ["--select", "DocEntry,DocNum,DocTotal,TransNum,CreationDate,AttachmentEntry"])
                if rows:
                    p = rows[-1]
                    d["posted"] = {"entity": ent, "doc_entry": p.get("DocEntry"), "doc_num": p.get("DocNum"),
                                   "total": p.get("DocTotal"), "journal": p.get("TransNum"),
                                   "attachment_row": p.get("AttachmentEntry")}
            except Exception:
                pass
    return orphan_rows


# --------------------------------------------------------------- transcripts
def project_dir():
    enc = "-" + ROOT.strip("/").replace("/", "-")
    return os.path.expanduser("~/.claude/projects/" + enc)


def text_blocks(content):
    if isinstance(content, str):
        return [content]
    out = []
    if isinstance(content, list):
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                out.append(b.get("text", ""))
    return out


def read_transcripts(date):
    pdir = project_dir()
    sessions = []
    for f in glob.glob(os.path.join(pdir, "*.jsonl")):
        st = os.stat(f)
        if dt.date.fromtimestamp(st.st_mtime).isoformat() != date or st.st_size < 50_000:
            continue
        first_user, texts = None, []
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                m = d.get("message") or {}
                if d.get("type") == "user" and first_user is None:
                    for t in text_blocks(m.get("content")):
                        t = t.strip()
                        if t and not t.startswith("<") and not t.startswith("Base directory for this skill"):
                            first_user = t[:240].replace("\n", " ")
                            break
                elif d.get("type") == "assistant":
                    for t in text_blocks(m.get("content")):
                        if len(t) > 200:
                            texts.append(t)
        tail = texts[-4:]
        final = max(tail, key=len) if tail else ""
        sessions.append({"file": os.path.basename(f), "last_write": dt.datetime.fromtimestamp(st.st_mtime).strftime("%H:%M"),
                         "first_user": first_user or "", "final_report": final, "n_texts": len(texts)})
    sessions.sort(key=lambda s: s["last_write"])
    return sessions


# ------------------------------------------------------------------- screens
def read_screens():
    """On a box with cmux: capture every terminal surface (title + last 45 lines)
    so a still-running session can be matched to its tab by content."""
    if not shutil.which("cmux"):
        return ""
    env = dict(os.environ, CMUX_QUIET="1")
    try:
        tree = subprocess.run(["cmux", "tree"], capture_output=True, text=True, timeout=20, env=env).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""
    L = ["# cmux screens at %s (last 45 lines of every terminal tab)" % dt.datetime.now().strftime("%H:%M"), ""]
    for m in re.finditer(r"surface (surface:\d+) \[terminal\] \"(.*?)\"(.*)", tree):
        ref, title, rest = m.group(1), m.group(2), m.group(3)
        try:
            scr = subprocess.run(["cmux", "read-screen", "--surface", ref, "--lines", "45"],
                                 capture_output=True, text=True, timeout=20, env=env).stdout
        except (OSError, subprocess.TimeoutExpired):
            scr = "(read-screen failed)"
        L.append("## %s  %s%s" % (ref, title, "  (this session)" if "here" in rest else ""))
        L.append("")
        L.append("```")
        L.append("\n".join(l for l in scr.splitlines() if l.strip())[:4000])
        L.append("```")
        L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------ skeleton
def state_of(d):
    if d.get("deleted"):
        s = "DELETED %s by %s" % ((d.get("deleted_at") or "")[11:16], d.get("deleted_by") or "?")
        if d.get("rebuilt_as"):
            s += ", rebuilt as %s" % d["rebuilt_as"]
        return s
    if d.get("posted"):
        return "POSTED LIVE as %s %s%s" % (d["posted"]["entity"].rstrip("s").replace("Purchase", "A/P "), d["posted"]["doc_entry"],
                                          (", journal %s" % d["posted"]["journal"]) if d["posted"].get("journal") else "")
    if d.get("sap_error"):
        return "NOT FOUND in Drafts: " + d["sap_error"]
    if d.get("auth") == "dasPending" or (d.get("approval") and d["approval"].get("status") == "ardPending"):
        return "With approver (pending)"
    if d.get("auth") == "dasApproved":
        return "Approved, awaiting Add"
    if d.get("auth") == "dasRejected":
        return "REJECTED by approver"
    if d.get("submitted_at") and d.get("submit_status") == 204:
        return "Submitted (verify approval status)"
    return "Held, not submitted"


def lines_grpos(d):
    n, g = d.get("lines"), d.get("n_grpo")
    if n is None:
        return "?"
    out = "%d line%s" % (n, "" if n == 1 else "s")
    return out + (" off %d GRPO%s" % (g, "" if g == 1 else "s") if g else ", no GRPO link")


def skeleton(date, docs, errors, deletes, sessions, log_rows, orphan_rows=()):
    for d in docs.values():
        if d.get("deleted") and not d.get("card_name"):
            d["card_name"] = "(deleted draft, no read-back possible)"
            d["bill_no"] = "see session report"
    order = sorted(docs.values(), key=lambda d: (d.get("card_name") or "~", str(d.get("bill_no") or ""), d["company"], d["doc_entry"]))
    n_new = sum(1 for d in order if d.get("created_at"))
    n_touched = len(order) - n_new
    times = [r["time"] for r in log_rows]
    first, last = (times[0][11:16], times[-1][11:16]) if times else ("", "")
    total = sum((d.get("total") or 0) for d in order if not d.get("deleted"))
    by_co = {}
    for d in order:
        if not d.get("deleted"):
            by_co[d["company"]] = by_co.get(d["company"], 0) + (d.get("total") or 0)
    n_lines = sum(d.get("lines") or 0 for d in order)
    n_grpo = sum(d.get("n_grpo") or 0 for d in order)
    pending = sum(1 for d in order if state_of(d).startswith("With approver"))
    posted = sum(1 for d in order if d.get("posted"))

    L = []
    L.append("# A/P entries made on %s" % ddmmyyyy(date))
    L.append("")
    L.append("TODO one line: who this is for and what was handed over. Every figure below was read back live from SAP at %s on %s." % (dt.datetime.now().strftime("%H:%M"), ddmmyyyy(date)))
    L.append("")
    L.append("## Master list: every number to find these in SAP")
    L.append("")
    L.append("Look up drafts by **DocEntry** (Purchasing → Document Drafts, set User to All). A draft's DocNum is provisional: it shows the next free number in its series at the time of saving, so several drafts can share one. The real number is assigned when the draft is Added.")
    L.append("")
    L.append("| # | Vendor | Bill no | Bill date | Book | Draft DocEntry | DocNum | Series | Branch |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for i, d in enumerate(order, 1):
        de = "**%s**" % d["doc_entry"]
        if d.get("posted"):
            de = "%s → **Invoice %s**" % (d["doc_entry"], d["posted"]["doc_entry"])
        L.append("| %d | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            i, d.get("card_name") or "?", d.get("bill_no") or "?", ddmmyyyy(d.get("doc_date")), d["company"], de,
            d.get("doc_num") or "", d.get("series") or "", d.get("branch") or ""))
    L.append("")
    L.append("| # | Draft | Vendor code | Amount | TDS | Lines / GRPOs | Attachment row | Approval request | State |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for i, d in enumerate(order, 1):
        ap = d.get("approval")
        aptxt = ("**%s**" % ap["code"]) if ap and ap.get("code") else ("none, posted live" if d.get("posted") else "none")
        att = d.get("attachment_row") or "none yet"
        if d.get("posted") and d["posted"].get("attachment_row"):
            att = "%s (draft: %s)" % (d["posted"]["attachment_row"], d.get("attachment_row") or "none")
        label = ("%s inv %s" % (d["company"], d["posted"]["doc_entry"])) if d.get("posted") else "%s %s" % (d["company"], d["doc_entry"])
        L.append("| %d | %s | %s | %s | %s | %s / %s | %s | %s | %s |" % (
            i, label, d.get("card_code") or "", inr(d.get("total")), inr(d.get("tds")) if d.get("tds") else "0",
            d.get("lines", "?") if d.get("lines") is not None else "?", d.get("n_grpo", "?") if d.get("n_grpo") is not None else "?", att, aptxt, state_of(d)))
    L.append("")
    L.append("Total across %d documents: %s. %s." % (
        len(order), inr(total), ", ".join("%s %s" % (k, inr(v)) for k, v in sorted(by_co.items()))))
    L.append("")
    users = sorted({d.get("created_by") for d in order if d.get("created_by")})
    L.append("Made under %s. %d new drafts today, %d older drafts touched (submitted, patched, or a scan appended). First write %s, last write %s. %d lines drawn from %d GRPOs. %d with the approver, %d posted." % (
        ", ".join(users) or "?", n_new, n_touched, first, last, n_lines, n_grpo, pending, posted))
    L.append("")
    touched = [d for d in order if d.get("touched")]
    if touched:
        L.append("Older drafts that only received an attachment today: " + ", ".join("%s %s (%s)" % (d["company"], d["doc_entry"], d["touched"]) for d in touched) + ".")
        L.append("")
    if orphan_rows:
        L.append("Attachment rows written today that no draft points at (an abandoned first attempt, or a row on a posted document): " + ", ".join("%s row %d at %s by %s" % (o["company"], o["row"], o["time"][11:16], o["user"]) for o in orphan_rows) + ".")
        L.append("")
    L.append("## What the reader needs to do")
    L.append("")
    L.append("TODO: group by action. Oil drafts submit from the CLI (`sapb1 add-draft <DocEntry>`); Mart and Beverages drafts must be Added from the SAP client because their DI approval switch is off (C-0074). Approval by the approver does not post: a person presses Add again.")
    L.append("")
    L.append("## Bill by bill")
    L.append("")
    for i, d in enumerate(order, 1):
        L.append("### %d. %s, bill %s, dated %s" % (i, d.get("card_name") or "?", d.get("bill_no") or "?", ddmmyyyy(d.get("doc_date"))))
        L.append("")
        L.append("| | |")
        L.append("|---|---|")
        L.append("| Draft | %s %s, DocNum %s, series %s, branch %s |" % (d["company"], d["doc_entry"], d.get("doc_num"), d.get("series"), d.get("branch")))
        L.append("| Vendor | %s |" % (d.get("card_code") or ""))
        L.append("| Amount | %s, %s |" % (inr(d.get("total")), lines_grpos(d)))
        L.append("| Tax | header VAT %s |" % inr(d.get("vat") or 0))
        L.append("| TDS | %s%s |" % (inr(d.get("tds")) if d.get("tds") else "Zero", (" (code %s)" % ", ".join(d["tds_codes"])) if d.get("tds_codes") else ""))
        L.append("| Attachments | row %s |" % (d.get("attachment_row") or "none yet"))
        L.append("| Status | %s |" % state_of(d))
        L.append("")
        if d.get("comments"):
            L.append("Draft comments: %s" % d["comments"][:400].replace("|", "/"))
            L.append("")
        L.append("TODO: open items from the session report (debit notes, TDS judgment, handwriting, rate marks).")
        L.append("")
    L.append("## Warnings and notices raised by each session")
    L.append("")
    L.append("Everything the entering session flagged, bill by bill. Condense from sessions.md; keep every warning, drop the narration.")
    L.append("")
    L.append("| # | Bill | Warning or notice |")
    L.append("|---|---|---|")
    for i, d in enumerate(order, 1):
        L.append("| %d | %s %s, %s %s | TODO |" % (i, d.get("card_name") or "?", d.get("bill_no") or "?", d["company"], d["doc_entry"]))
    L.append("| all | General | A draft's DocNum is provisional. Find drafts by DocEntry. |")
    L.append("")
    if errors:
        L.append("## SAP errors seen in the write log")
        L.append("")
        L.append("| Time | User | Book | Call | Error |")
        L.append("|---|---|---|---|---|")
        for e in errors:
            L.append("| %s | %s | %s | %s %s | %s |" % (e["time"][11:16], e["user"], e["company"], e["method"], e["path"], (e.get("error") or "")[:160].replace("|", "/")))
        L.append("")
    if deletes:
        L.append("## Drafts deleted today")
        L.append("")
        for x in deletes:
            L.append("- %s %s at %s by %s" % (x["company"], x["doc_entry"], x["time"][11:16], x["user"]))
        L.append("")
    L.append("Every write is in the shared log under the operator's name (queries/<operator>/sap-writes.jsonl).")
    L.append("")
    return "\n".join(L)


def sessions_md(sessions):
    L = ["# What each session reported (%d sessions active today)" % len(sessions), ""]
    for s in sessions:
        L.append("## %s  (last write %s, %d reports)" % (s["file"][:8], s["last_write"], s["n_texts"]))
        L.append("")
        L.append("First ask: %s" % s["first_user"])
        L.append("")
        L.append(s["final_report"] or "(no final report yet: session still running, use SAP read-back and its screen)")
        L.append("")
    return "\n".join(L)


# -------------------------------------------------------------------- render
def md_to_html(md_text, title):
    src = md_text.splitlines()

    def inline(t):
        t = html.escape(t, quote=False)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
        t = re.sub(r"~~(.+?)~~", r"<s>\1</s>", t)
        return t

    out, i, n = [], 0, len(src)
    while i < n:
        l = src[i]
        if l.startswith("|"):
            rows = []
            while i < n and src[i].startswith("|"):
                rows.append(src[i])
                i += 1
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            hdr, body = cells[0], cells[2:]
            hj = " ".join(hdr)
            if "DocEntry" in hj or "Approval request" in hj:
                cls = "master"
            elif len(hdr) == 3 and "Warning" in hj:
                cls = "warn"
            elif len(hdr) == 2 and not hdr[0]:
                cls = "kv"
            else:
                cls = "plain"
            out.append('<table class="%s"><thead><tr>' % cls + "".join("<th>%s</th>" % inline(h) for h in hdr) + "</tr></thead><tbody>")
            for r in body:
                out.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            out.append("</tbody></table>")
            continue
        if l.startswith("- "):
            out.append("<ul>")
            while i < n and src[i].startswith("- "):
                out.append("<li>%s</li>" % inline(src[i][2:]))
                i += 1
            out.append("</ul>")
            continue
        if l.startswith("```"):
            i += 1
            buf = []
            while i < n and not src[i].startswith("```"):
                buf.append(html.escape(src[i]))
                i += 1
            i += 1
            out.append("<pre>%s</pre>" % "\n".join(buf))
            continue
        m = re.match(r"^(#{1,3}) (.*)", l)
        if m:
            out.append("<h%d>%s</h%d>" % (len(m.group(1)), inline(m.group(2)), len(m.group(1))))
            i += 1
            continue
        if not l.strip():
            i += 1
            continue
        para = [l]
        i += 1
        while i < n and src[i].strip() and not src[i].startswith(("|", "#", "- ", "```")):
            para.append(src[i])
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(para)))
    css = """
@page { size: A4; margin: 14mm 12mm 16mm 12mm; }
body { font-family: Helvetica, Arial, sans-serif; font-size: 9.6pt; line-height: 1.35; color:#111; margin:0; }
h1 { font-size: 17pt; margin: 0 0 6px 0; }
h2 { font-size: 12.5pt; margin: 16px 0 6px 0; border-bottom: 1px solid #999; padding-bottom: 2px; break-after: avoid; }
h3 { font-size: 10.5pt; margin: 12px 0 4px 0; break-after: avoid; }
p { margin: 4px 0 7px 0; }
code { font-family: Menlo, monospace; font-size: 8.6pt; background:#f2f2f2; padding:0 2px; }
pre { font-family: Menlo, monospace; font-size: 8.6pt; background:#f2f2f2; padding:6px; }
table { border-collapse: collapse; width: 100%; margin: 4px 0 10px 0; font-size: 8.4pt; }
th, td { border: 1px solid #bbb; padding: 2.5px 4px; vertical-align: top; text-align: left; }
th { background: #e9e9e9; font-weight: bold; }
tr { break-inside: avoid; }
thead { display: table-header-group; }
table.master td:nth-child(1), table.master th:nth-child(1) { width: 2.4em; }
table.master td { white-space: nowrap; }
table.master td:last-child { white-space: normal; }
table.kv td:first-child { width: 22%; font-weight: bold; background:#f7f7f7; }
table.warn td:nth-child(1) { width: 2.4em; white-space: nowrap; }
table.warn td:nth-child(2) { width: 15%; }
tbody tr:nth-child(even) td { background: #fafafa; }
ul { margin: 2px 0 8px 18px; padding:0; }
li { margin: 2px 0; }
"""
    return ("<!doctype html><html><head><meta charset='utf-8'><title>%s</title><style>%s</style></head><body>%s</body></html>"
            % (html.escape(title), css, "\n".join(out)))


def render(md_path, pdf_path=None, downloads=True):
    md_path = os.path.abspath(md_path)
    md_text = open(md_path, encoding="utf-8").read()
    m = re.search(r"^# (.+)$", md_text, re.M)
    title = m.group(1) if m else os.path.basename(md_path)
    work = os.path.dirname(md_path)
    base = os.path.splitext(os.path.basename(md_path))[0]
    html_path = os.path.join(work, base + ".html")
    open(html_path, "w", encoding="utf-8").write(md_to_html(md_text, title))
    # browse can only write under /private/tmp or the repo; render there, copy after
    tmp_pdf = os.path.join(work, base + ".pdf")
    if not (work.startswith("/private/tmp") or work.startswith("/tmp") or work.startswith(ROOT)):
        tmp_pdf = os.path.join("/private/tmp", base + ".pdf")
    if not os.path.exists(BROWSE):
        sys.exit("gstack browse binary not found at %s; run ./setup in the gstack repo" % BROWSE)
    subprocess.run([BROWSE, "goto", "file://" + html_path], check=True, capture_output=True, text=True, timeout=90)
    p = subprocess.run([BROWSE, "pdf", tmp_pdf], capture_output=True, text=True, timeout=120)
    if p.returncode != 0 or not os.path.exists(tmp_pdf):
        sys.exit("browse pdf failed: " + (p.stderr or p.stdout))
    final = pdf_path or (os.path.join(os.path.expanduser("~/Downloads"), base + ".pdf") if downloads else tmp_pdf)
    if os.path.abspath(final) != os.path.abspath(tmp_pdf):
        shutil.copyfile(tmp_pdf, final)
    pages = ""
    try:
        info = subprocess.run(["pdfinfo", final], capture_output=True, text=True).stdout
        mm = re.search(r"Pages:\s+(\d+)", info)
        pages = (" (%s pages)" % mm.group(1)) if mm else ""
    except OSError:
        pass
    print(final + pages)


# ---------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--date", default=dt.date.today().isoformat())
    c.add_argument("--out", default=None)
    c.add_argument("--no-sap", action="store_true")
    c.add_argument("--no-transcripts", action="store_true")
    c.add_argument("--no-screens", action="store_true")
    r = sub.add_parser("render")
    r.add_argument("md")
    r.add_argument("--pdf", default=None)
    r.add_argument("--no-downloads", action="store_true")
    a = ap.parse_args()

    if a.cmd == "render":
        render(a.md, a.pdf, downloads=not a.no_downloads)
        return

    out = a.out or os.path.join(os.environ.get("TMPDIR", "/private/tmp"), "summary-pdf-" + a.date)
    os.makedirs(out, exist_ok=True)
    rows = read_write_logs(a.date)
    docs, errors, deletes, att_rows = digest_log(rows)
    print("write log: %d events, %d drafts touched, %d attachment rows, %d errors, %d deletes" % (len(rows), len(docs), len(att_rows), len(errors), len(deletes)), file=sys.stderr)
    orphan_rows = []
    if not a.no_sap and (docs or att_rows):
        orphan_rows = readback(docs, att_rows)
        print("SAP read-back done (%d found, %d attachment-only, %d orphan rows)" % (
            sum(1 for d in docs.values() if d.get("doc_num")), sum(1 for d in docs.values() if d.get("touched")), len(orphan_rows)), file=sys.stderr)
    sessions = [] if a.no_transcripts else read_transcripts(a.date)
    print("transcripts: %d sessions active on %s" % (len(sessions), a.date), file=sys.stderr)
    screens = "" if a.no_screens else read_screens()
    if screens:
        open(os.path.join(out, "screens.md"), "w", encoding="utf-8").write(screens)
        print("screens: captured (screens.md)", file=sys.stderr)
    with open(os.path.join(out, "entries.json"), "w", encoding="utf-8") as fh:
        json.dump({"date": a.date, "docs": list(docs.values()),
                   "orphan_attachment_rows": orphan_rows, "errors": errors, "deletes": deletes,
                   "sessions": [{k: v for k, v in s.items() if k != "final_report"} for s in sessions]}, fh, indent=1, ensure_ascii=False)
    open(os.path.join(out, "skeleton.md"), "w", encoding="utf-8").write(skeleton(a.date, docs, errors, deletes, sessions, rows, orphan_rows))
    open(os.path.join(out, "sessions.md"), "w", encoding="utf-8").write(sessions_md(sessions))
    print(out)


if __name__ == "__main__":
    main()
