#!/usr/bin/env python3
"""
alerts.py — shout once when a rejected entry crosses 2 days, and once when it
finally clears. Never in between.

The latch is the whole point: this runs every minute, so without it the same
document would be reported 1,440 times a day and everyone would mute it. Same
edge-triggered shape as jolly/live/chain_status.py.

Only entries rejected AFTER the board went live can alarm (build.py sets
"alarmable"). Otherwise the first run would fire about the 56 entries that were
already stale on day one, several of them well over a year old, and the alarm
would mean nothing from the very first morning.
"""
import argparse, json, os, sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import whatsapp                                                  # noqa: E402

IST   = timezone(timedelta(hours=5, minutes=30))
ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state")
BOOKNAME = {"OIL": "Oil", "MART": "Mart", "BEV": "Beverages"}


def rupees(n):
    """Indian grouping, no paise — 177000 -> 1,77,000"""
    n = int(round(n))
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if n < 0 else "") + s


def load(name, default):
    try:
        with open(os.path.join(STATE, name), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def save(name, obj):
    os.makedirs(STATE, exist_ok=True)
    path = os.path.join(STATE, name)
    with open(path + ".tmp", "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
    os.replace(path + ".tmp", path)


def line(r):
    days = (r["age_hours"] or 0) / 24.0
    return "%s %s · %s · Rs %s · %s · %.1f days · \"%s\"" % (
        BOOKNAME.get(r["book"], r["book"]), r["doc_entry"], r["vendor"][:28],
        rupees(r["amount"]), r["who"], days, (r["reason"] or "no reason given")[:40])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="print what would be sent; send nothing, latch nothing")
    args = ap.parse_args()

    board = load("board.json", None)
    if not board:
        print("alerts: no board.json yet")
        return 0

    latch = load("alerted.json", {})
    rows = {r["id"]: r for b in board["books"].values() for r in b["rows"]}
    late_h = board.get("late_after_hours", 48)
    rec = whatsapp.recipients()

    # --- newly late -------------------------------------------------------
    newly = [r for rid, r in rows.items()
             if r.get("alarmable") and (r["age_hours"] or 0) >= late_h and rid not in latch]
    # --- alerted before, now gone from the board = somebody dealt with it ---
    cleared = [rid for rid in latch if rid not in rows]

    if args.dry_run:
        print("would alert on %d newly late, %d cleared" % (len(newly), len(cleared)))
        for r in sorted(newly, key=lambda x: -(x["age_hours"] or 0)):
            print("  LATE    " + line(r))
        for rid in cleared:
            print("  CLEARED " + rid + "  " + (latch[rid].get("vendor") or ""))
        return 0

    if newly:
        body = ("JIVO approvals — %d rejected %s past 2 days and still not fixed:\n\n%s"
                "\n\nBhawani rejected these; they need re-doing. Board: %s" % (
                    len(newly), "entries are" if len(newly) > 1 else "entry is",
                    "\n".join(line(r) for r in sorted(newly, key=lambda x: -(x["age_hours"] or 0))),
                    os.environ.get("APPROVAL_BOARD_URL", "https://jivo-approvals.vercel.app")))
        whatsapp.send(rec.get("group"), body, why="late>%dh" % late_h)
        for r in newly:
            latch[r["id"]] = {"alerted_at": datetime.now(IST).isoformat(),
                              "vendor": r["vendor"], "who": r["who"],
                              "amount": r["amount"], "book": r["book"]}

    for rid in cleared:
        was = latch.pop(rid)
        whatsapp.send(rec.get("group"),
                      "JIVO approvals — cleared: %s %s (%s, Rs %s) is off the board." % (
                          BOOKNAME.get(was.get("book"), was.get("book", "")),
                          rid.split("-")[-1], was.get("vendor", ""), rupees(was.get("amount", 0))),
                      why="cleared")

    save("alerted.json", latch)
    if newly or cleared:
        print("alerts: %d newly late, %d cleared (latched %d)" % (len(newly), len(cleared), len(latch)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
