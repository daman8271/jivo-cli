#!/usr/bin/env python3
"""jolly_wa — the live loop: a WhatsApp message to Jivo AI → the Jolly agent → a reply.

Reads jwa's archive (never WhatsApp itself), answers only people who were named
with `jwa name` (naming someone IS allowing them), runs Claude Code headless in
the planner folder with one conversation per person, and sends the answer back
through the daemon's loopback API — the one door out of this box.

    jolly_wa.py              the loop (systemd runs it)
    jolly_wa.py --dry "…"    answer one question on stdout, send nothing
"""
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.request

HOME = os.environ.get("JWA_HOME", os.path.expanduser("~/.jwa"))
ARCHIVE = os.path.join(HOME, "archive.db")
STATE = os.path.join(HOME, "agent-state.json")
API = os.environ.get("JWA_API", "127.0.0.1:3012")
WORKDIR = os.environ.get("JOLLY_DIR", os.path.expanduser("~/jivo-cli/jolly"))
CLAUDE = os.environ.get("CLAUDE_BIN", "claude")
TOOLS = os.environ.get("JOLLY_TOOLS", "Read,Glob,Grep")
POLL_S = 2.0
CLAUDE_TIMEOUT_S = 300
MAX_REPLY = 3500

SYSTEM = """You are Jivo AI, JIVO's assistant on WhatsApp. You are replying to {name}.
You are inside JIVO's September production planner (the folder you are in). Read CLAUDE.md there before answering anything about the plan, and take every figure from the files — never from memory.
Write like a WhatsApp message: plain language, short, the number first and one line on where it came from. No markdown, no headers, no tables, no code blocks, no bullet symbols, no asterisks. Indian number grouping, litres as L, big money in crores.
If you did not read a figure from a file, say you do not have it rather than guessing. If asked to change, re-run or deploy anything, say that only reading is switched on today and Daman can switch on more."""

SORRY = "Sorry, I could not work that out just now. Daman has been told."


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), msg, flush=True)


def user_of(jid):
    return jid.split("@", 1)[0].split(":", 1)[0]


def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except (OSError, ValueError):
        # First start: answer only what arrives from now on, never the backlog.
        return {"since": int(time.time()), "seen": [], "sessions": {}}


def save_state(st):
    st["seen"] = st["seen"][-500:]
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f)
    os.replace(tmp, STATE)


def names(con):
    """jid_user -> (name, phone). Being in this table is the allowlist."""
    return {r[0]: (r[1], r[2]) for r in con.execute("SELECT jid_user, name, phone FROM names")}


def me(con):
    row = con.execute("SELECT sender_jid FROM messages WHERE from_me = 1 ORDER BY ts DESC LIMIT 1").fetchone()
    return user_of(row[0]) if row else ""


def new_messages(con, since, seen):
    rows = con.execute(
        """SELECT id, chat_jid, sender_jid, ts, body, media_type, media_path, media_name
           FROM messages WHERE from_me = 0 AND is_group = 0 AND ts >= ? ORDER BY ts, rowid""",
        (since,))
    return [r for r in rows if r[0] not in seen]


def ask(name, text, media, session_id):
    prompt = text.strip()
    if media:
        mtype, mpath, mname = media
        prompt += f"\n\n[{name} attached a {mtype}: {mpath} ({mname}). Read it if it matters to the question.]"
    if not prompt:
        prompt = "[empty message]"
    cmd = [CLAUDE, "-p", prompt, "--output-format", "json",
           "--append-system-prompt", SYSTEM.format(name=name),
           "--allowedTools", TOOLS]
    if session_id:
        cmd += ["--resume", session_id]
    r = subprocess.run(cmd, cwd=WORKDIR, capture_output=True, text=True, timeout=CLAUDE_TIMEOUT_S)
    if r.returncode != 0 and session_id:
        log(f"resume of {session_id} failed ({r.stderr.strip()[:120]}); starting a fresh conversation")
        return ask(name, text, media, None)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[:300] or f"claude exited {r.returncode}")
    d = json.loads(r.stdout)
    if d.get("is_error"):
        raise RuntimeError(str(d.get("result"))[:300])
    return (d.get("result") or "").strip(), d.get("session_id") or session_id


def send(to, text):
    body = json.dumps({"to": to, "text": text[:MAX_REPLY]}).encode()
    req = urllib.request.Request(f"http://{API}/send", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.load(resp).get("id")


def handle(con, st, row):
    mid, chat_jid, sender_jid, ts, body, mtype, mpath, mname = row
    who = user_of(sender_jid)
    people = names(con)
    if who not in people:
        log(f"ignored {mid} from {who}: not named (jwa name <number> <label> to allow)")
        return
    name, phone = people[who]
    media = (mtype, mpath, mname) if mtype else None
    log(f"{name}: {body[:80]!r}{' +' + mtype if mtype else ''}")
    to = phone or chat_jid
    try:
        reply, sid = ask(name, body or "", media, st["sessions"].get(who))
        if sid:
            st["sessions"][who] = sid
        if not reply:
            reply = SORRY
    except (subprocess.TimeoutExpired, RuntimeError, ValueError) as e:
        log(f"! claude failed for {name}: {e}")
        reply = SORRY
    sent = send(to, reply)
    log(f"→ {name} ({sent}): {reply[:80]!r}")


def loop():
    st = load_state()
    log(f"jolly-wa up: answering people in jwa's names table, planner at {WORKDIR}, tools {TOOLS}")
    while True:
        try:
            con = sqlite3.connect(f"file:{ARCHIVE}?mode=ro", uri=True, timeout=10)
            try:
                rows = new_messages(con, st["since"], set(st["seen"]))
                mine = me(con)
                for row in rows:
                    st["seen"].append(row[0])
                    st["since"] = max(st["since"], row[3])
                    save_state(st)
                    if user_of(row[2]) == mine:
                        continue  # our own number talking to itself
                    handle(con, st, row)
                    save_state(st)
            finally:
                con.close()
        except Exception as e:  # noqa: BLE001 — the loop must not die on one bad turn
            log(f"! loop error: {e}")
            time.sleep(5)
        time.sleep(POLL_S)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--dry":
        reply, sid = ask("Daman (test)", " ".join(sys.argv[2:]), None, None)
        print(reply)
        print(f"\n[session {sid}]", file=sys.stderr)
    else:
        loop()
