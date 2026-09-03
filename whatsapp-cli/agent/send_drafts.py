#!/usr/bin/env python3
"""send_drafts — one day's planner WhatsApp drafts, sent for real through Jivo AI.

The planner writes sim/whatsapp-sep.json: for each person, the messages it would
send, dated. From 2026-09-03 they go out for real. This posts a day's drafts to
the jwa daemon's loopback /send, one at a time with a human pause between them,
records every send in ~/.jwa/sent-drafts.jsonl and never sends the same draft
twice (date + number + text hash).

    send_drafts.py                       dry run for today (IST): prints, sends nothing
    send_drafts.py --date 2026-09-03     dry run for that day
    send_drafts.py --yes                 send today's
    send_drafts.py --yes --copy-to +91…  and send Daman a copy of each
    send_drafts.py --only Gautam         just that person's

Numbers come from the planner's own people list; nothing is typed here.
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
HOME = os.environ.get("JWA_HOME", os.path.expanduser("~/.jwa"))
API = os.environ.get("JWA_API", "127.0.0.1:3012")
JOLLY = os.environ.get("JOLLY_DIR", os.path.expanduser("~/jivo-cli/jolly"))
DRAFTS = os.path.join(JOLLY, "sim", "whatsapp-sep.json")
LEDGER = os.path.join(HOME, "sent-drafts.jsonl")
ARCHIVE = os.path.join(HOME, "archive.db")
PAUSE_S = 45


def key(date, number, text):
    return hashlib.sha256(f"{date}|{number}|{text}".encode()).hexdigest()[:16]


def already_sent():
    keys = set()
    try:
        with open(LEDGER) as f:
            for ln in f:
                try:
                    keys.add(json.loads(ln)["key"])
                except (ValueError, KeyError):
                    pass
    except OSError:
        pass
    return keys


def has_written_to_us(number):
    """True if this number has ever sent us a message — the only people a
    day-old number may write to. On 2026-09-03 07:30 the first send to a
    number that had never messaged us got the device logged out 3 s later."""
    import sqlite3
    digits = "".join(ch for ch in str(number) if ch.isdigit())
    try:
        con = sqlite3.connect(f"file:{ARCHIVE}?mode=ro", uri=True, timeout=10)
        try:
            n = con.execute("""SELECT COUNT(*) FROM messages
                               WHERE from_me = 0 AND (sender_jid LIKE ? OR sender_jid IN
                               (SELECT jid_user || '%' FROM names WHERE phone LIKE ?))""",
                            (digits + "@%", "%" + digits)).fetchone()[0]
            if n:
                return True
            # a LID-keyed sender whose phone we learned via the names table
            lids = [r[0] for r in con.execute("SELECT jid_user FROM names WHERE phone LIKE ?", ("%" + digits,))]
            for lid in lids:
                if con.execute("SELECT 1 FROM messages WHERE from_me = 0 AND sender_jid LIKE ? LIMIT 1", (lid + "%",)).fetchone():
                    return True
            return False
        finally:
            con.close()
    except Exception:  # noqa: BLE001
        return False


def send(to, text):
    body = json.dumps({"to": to, "text": text}).encode()
    req = urllib.request.Request(f"http://{API}/send", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.load(resp)["id"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now(IST).strftime("%Y-%m-%d"))
    ap.add_argument("--yes", action="store_true", help="really send (default is a dry run)")
    ap.add_argument("--only", default="", help="only this person (substring of the name)")
    ap.add_argument("--copy-to", default="", help="also send each message to this number")
    ap.add_argument("--first-contact", action="store_true",
                    help="allow writing to a number that has never messaged us (risky on a young number)")
    a = ap.parse_args()

    threads = json.load(open(DRAFTS))
    todo = []
    for t in threads:
        if a.only and a.only.lower() not in t["name"].lower():
            continue
        for m in t.get("messages", []):
            if m.get("day") == a.date and m.get("dir", "out") == "out":
                todo.append((t["name"], t["whatsapp"], m.get("tag", ""), m["text"]))
    if not todo:
        print(f"{a.date}: nothing to send — no drafts dated that day")
        return 0

    done = already_sent()
    print(f"{a.date}: {len(todo)} draft(s){'' if a.yes else '  [DRY RUN — nothing sent]'}\n")
    sent = 0
    for name, number, tag, text in todo:
        k = key(a.date, number, text)
        print(f"── {name}  …{str(number)[-4:]}  [{tag}]{'  ALREADY SENT' if k in done else ''}")
        print(text.rstrip() + "\n")
        if not a.yes or k in done:
            continue
        if not a.first_contact and not has_written_to_us(number):
            print(f"   ! skipped: {name} has never messaged this number — ask them to send Jivo AI a 'hi' first (or --first-contact)")
            with open(LEDGER, "a") as f:
                f.write(json.dumps({"key": k + "-skip", "date": a.date, "to": str(number), "name": name, "tag": tag,
                                    "skipped": "never messaged us", "at": datetime.now(IST).isoformat()}) + "\n")
            continue
        try:
            mid = send(str(number), text)
        except Exception as e:  # noqa: BLE001
            print(f"   ! not sent: {e}", file=sys.stderr)
            with open(LEDGER, "a") as f:
                f.write(json.dumps({"key": k, "date": a.date, "to": str(number), "name": name, "tag": tag,
                                    "error": str(e)[:200], "at": datetime.now(IST).isoformat()}) + "\n")
            continue
        with open(LEDGER, "a") as f:
            f.write(json.dumps({"key": k, "date": a.date, "to": str(number), "name": name, "tag": tag,
                                "id": mid, "at": datetime.now(IST).isoformat()}) + "\n")
        print(f"   sent {mid}")
        sent += 1
        if a.copy_to:
            try:
                send(a.copy_to, f"[copy of what went to {name}]\n\n{text}")
            except Exception as e:  # noqa: BLE001
                print(f"   ! copy not sent: {e}", file=sys.stderr)
        time.sleep(PAUSE_S)
    if a.yes:
        print(f"sent {sent} of {len(todo)}; ledger {LEDGER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
