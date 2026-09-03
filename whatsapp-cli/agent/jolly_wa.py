#!/usr/bin/env python3
"""jolly_wa — the live loop: a WhatsApp message to Jivo AI → the Jolly agent → a reply.

v2 (2026-09-02 night): built for speed the way Hermes/OpenClaw are.
  * one LIVE Claude Code session per person (Claude Agent SDK) — no process
    start per message, the conversation stays in memory, resumed after restarts
  * the gateway wakes us the instant a message lands (GET /wait), no polling gap
  * "typing…" is shown while the answer is being written
  * the planner summary rides in the system prompt, so most questions are one
    model call with no file reads

Reads jwa's archive (never WhatsApp itself), answers people who were named with
`jwa name` — naming someone IS allowing them — or everyone through
JOLLY_OPEN_UNTIL, and sends through the daemon's loopback API, the one door.

    jolly_wa.py              the loop (systemd runs it)
    jolly_wa.py --dry "…"    answer one question on stdout with timing, send nothing
"""
import asyncio
import json
import os
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from claude_agent_sdk.types import AssistantMessage, PermissionResultDeny, ResultMessage, TextBlock

IST = timezone(timedelta(hours=5, minutes=30))
HOME = os.environ.get("JWA_HOME", os.path.expanduser("~/.jwa"))
ARCHIVE = os.path.join(HOME, "archive.db")
STATE = os.path.join(HOME, "agent-state.json")
API = os.environ.get("JWA_API", "127.0.0.1:3012")
WORKDIR = os.environ.get("JOLLY_DIR", os.path.expanduser("~/jivo-cli/jolly"))
TOOLS = [t for t in os.environ.get("JOLLY_TOOLS", "Read,Glob,Grep").split(",") if t]
OPEN_UNTIL = os.environ.get("JOLLY_OPEN_UNTIL", "").strip()   # answer EVERYONE through this IST date
EFFORT = os.environ.get("JOLLY_EFFORT", "low")                  # low = fastest replies
SUMMARY_FILE = os.environ.get("JOLLY_SUMMARY", os.path.join(WORKDIR, "SEPTEMBER-HANDOFF.md"))
IDLE_CLOSE_S = 20 * 60
MAX_REPLY = 3500
SAFETY_POLL_S = 25

SYSTEM = """You are Jivo AI, JIVO's assistant on WhatsApp. You are replying to {name}.
You are inside JIVO's September production planner (the folder you are in; its CLAUDE.md is loaded). Below is the planner's own summary — answer from it directly when it has the figure; open a file only when it does not.
Write like a WhatsApp message: plain language, short, the number first and one line on where it came from. No markdown, no headers, no tables, no code blocks, no bullet symbols, no asterisks. Indian number grouping, litres as L, big money in crores. Answer in the language they wrote in — Hindi or Punjabi in Roman letters is normal here; keep it that way.
The recent messages of this chat are given with each message, including ones Jivo AI sent (the daily build list and exception notes come from the planner). A short reply like "ok", "done" or "line band hai" is about the last thing we sent — answer it in that light, and if it reports a problem, acknowledge it plainly and say Daman will see it.
You have NO live connection to SAP, the factory app, EXIM or any system — only the planner's files in this folder. Never say or imply you are connected to SAP or can check anything live; if asked, say the planner files are as of the last freeze and Daman can pull live numbers.
If you did not read a figure from the summary or a file, say you do not have it rather than guessing. If asked to change, re-run or deploy anything, say that only reading is switched on today and Daman can switch on more.

=== PLANNER SUMMARY ({summary_name}) ===
{summary}
=== END SUMMARY ==="""

SORRY = "Sorry, I could not work that out just now. Daman has been told."


def log(msg):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), msg, flush=True)


def user_of(jid):
    return jid.split("@", 1)[0].split(":", 1)[0]


def open_today():
    return bool(OPEN_UNTIL) and datetime.now(IST).strftime("%Y-%m-%d") <= OPEN_UNTIL


def load_state():
    try:
        with open(STATE) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"since": int(time.time()), "seen": [], "sessions": {}}


def save_state(st):
    st["seen"] = st["seen"][-500:]
    tmp = STATE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f)
    os.replace(tmp, STATE)


def summary_text():
    try:
        with open(SUMMARY_FILE, encoding="utf-8") as f:
            return f.read()[:40000]
    except OSError:
        return "(no summary file found — read the planner files)"


def names(con):
    return {r[0]: (r[1], r[2]) for r in con.execute("SELECT jid_user, name, phone FROM names")}


def me(con):
    row = con.execute("SELECT sender_jid FROM messages WHERE from_me = 1 ORDER BY ts DESC LIMIT 1").fetchone()
    return user_of(row[0]) if row else ""


def new_messages(con, since, seen):
    rows = con.execute(
        """SELECT id, chat_jid, sender_jid, ts, body, media_type, media_path, media_name, sender_name
           FROM messages WHERE from_me = 0 AND is_group = 0 AND ts >= ? ORDER BY ts, rowid""", (since,))
    return [r for r in rows if r[0] not in seen]


def recent(con, chat_jid, limit=8):
    rows = con.execute(
        """SELECT from_me, body, ts FROM messages WHERE chat_jid = ? AND body <> ''
           ORDER BY ts DESC LIMIT ?""", (chat_jid, limit)).fetchall()
    return "\n".join(f"[{time.strftime('%d %b %H:%M', time.localtime(ts))}] {'Jivo AI' if fm else 'them'}: {b.strip()[:600]}"
                     for fm, b, ts in reversed(rows))


def api(path, payload=None, timeout=90):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(f"http://{API}{path}", data=data,
                                 headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


async def deny_everything_else(tool, _input, _ctx):
    return PermissionResultDeny(message=f"{tool} is not switched on for WhatsApp answers")


class Person:
    """One live Claude session per person."""

    def __init__(self, user, name, session_id):
        self.user, self.name, self.session_id = user, name, session_id
        self.client = None
        self.last_used = time.time()
        self.lock = asyncio.Lock()

    def options(self, resume):
        return ClaudeAgentOptions(
            cwd=WORKDIR,
            allowed_tools=TOOLS,
            disallowed_tools=["Bash", "Write", "Edit", "MultiEdit", "NotebookEdit", "WebFetch", "WebSearch", "Task", "Agent"],
            can_use_tool=deny_everything_else,
            system_prompt={"type": "preset", "preset": "claude_code",
                           "append": SYSTEM.format(name=self.name, summary=summary_text(),
                                                   summary_name=os.path.basename(SUMMARY_FILE))},
            setting_sources=["project"],
            resume=resume or None,
            max_turns=12,
            effort=EFFORT,
        )

    async def open(self, resume):
        self.client = ClaudeSDKClient(self.options(resume))
        await self.client.connect()
        log(f"session open for {self.name}{' (resumed)' if resume else ' (fresh)'}")

    async def close(self):
        if self.client:
            try:
                await self.client.disconnect()
            except Exception:  # noqa: BLE001
                pass
            self.client = None

    async def ask(self, prompt):
        async with self.lock:
            self.last_used = time.time()
            for attempt in (1, 2):
                try:
                    if self.client is None:
                        await self.open(self.session_id if attempt == 1 else None)
                    await self.client.query(prompt)
                    text, result = [], None
                    async for m in self.client.receive_response():
                        if isinstance(m, AssistantMessage):
                            text.extend(b.text for b in m.content if isinstance(b, TextBlock))
                        elif isinstance(m, ResultMessage):
                            result = m
                    if result and result.session_id:
                        self.session_id = result.session_id
                    if result and result.is_error:
                        raise RuntimeError(str(result.result)[:300])
                    reply = (result.result if result and result.result else "\n".join(text)).strip()
                    return reply, (result.duration_ms if result else None)
                except Exception as e:  # noqa: BLE001
                    log(f"! session for {self.name} failed (try {attempt}): {e}")
                    await self.close()
                    if attempt == 2:
                        raise
            return "", None


class Loop:
    def __init__(self):
        self.st = load_state()
        self.people = {}

    def person(self, user, name):
        p = self.people.get(user)
        if p is None:
            p = Person(user, name, self.st["sessions"].get(user))
            self.people[user] = p
        return p

    async def handle(self, con, row):
        mid, chat_jid, sender_jid, ts, body, mtype, mpath, mname, pushname = row
        who = user_of(sender_jid)
        people = names(con)
        if who in people:
            name, phone = people[who]
        elif open_today():
            name, phone = (pushname or who), ""
            log(f"open-policy (through {OPEN_UNTIL}): answering unnamed {who} as {name!r}")
        else:
            log(f"ignored {mid} from {who}: not named (jwa name <number> <label>, or JOLLY_OPEN_UNTIL=<date>)")
            return
        media = (mtype, mpath, mname) if mtype else None
        if not (body or "").strip() and not media:
            log(f"{name}: empty message {mid} — no reply")
            return
        log(f"{name}: {body[:80]!r}{' +' + mtype if mtype else ''}")
        to = phone or chat_jid

        prompt = (body or "").strip()
        if media:
            prompt += f"\n\n[{name} attached a {mtype}: {mpath} ({mname}). Read it if it matters.]"
        ctx = recent(con, chat_jid)
        if ctx:
            prompt = f"Recent messages in this WhatsApp chat (oldest first):\n{ctx}\n\nNew message from {name}:\n{prompt or '[no text]'}"

        try:
            api("/typing", {"to": to, "on": True}, timeout=10)
        except Exception:  # noqa: BLE001
            pass
        t0 = time.time()
        try:
            reply, model_ms = await self.person(who, name).ask(prompt)
            if not reply:
                reply = SORRY
        except Exception as e:  # noqa: BLE001
            log(f"! claude failed for {name}: {e}")
            reply, model_ms = SORRY, None
        self.st["sessions"][who] = self.people[who].session_id or self.st["sessions"].get(who)
        try:
            api("/typing", {"to": to, "on": False}, timeout=10)
        except Exception:  # noqa: BLE001
            pass
        sent = api("/send", {"to": to, "text": reply[:MAX_REPLY]}).get("id")
        log(f"→ {name} ({sent}) in {time.time() - t0:.1f}s (model {model_ms} ms): {reply[:80]!r}")

    async def drain(self):
        con = sqlite3.connect(f"file:{ARCHIVE}?mode=ro", uri=True, timeout=10)
        try:
            mine = me(con)
            for row in new_messages(con, self.st["since"], set(self.st["seen"])):
                self.st["seen"].append(row[0])
                self.st["since"] = max(self.st["since"], row[3])
                save_state(self.st)
                if user_of(row[2]) == mine:
                    continue
                await self.handle(con, row)
                save_state(self.st)
        finally:
            con.close()

    async def reaper(self):
        while True:
            await asyncio.sleep(60)
            for p in list(self.people.values()):
                if p.client and time.time() - p.last_used > IDLE_CLOSE_S and not p.lock.locked():
                    log(f"closing idle session for {p.name}")
                    await p.close()

    async def run(self):
        log(f"jolly-wa v2 up: live sessions, push wake, typing; named people"
            f"{' and EVERYONE through ' + OPEN_UNTIL if OPEN_UNTIL else ''}; planner {WORKDIR}; tools {TOOLS}; effort {EFFORT}")
        asyncio.create_task(self.reaper())
        while True:
            try:
                await self.drain()
                # block until the gateway says a message landed (≤25 s), then look again
                await asyncio.to_thread(lambda: api("/wait", timeout=SAFETY_POLL_S + 10))
            except Exception as e:  # noqa: BLE001
                log(f"! loop error: {e}")
                await asyncio.sleep(3)


async def dry(question):
    p = Person("dry", "Daman (test)", None)
    t0 = time.time()
    reply, model_ms = await p.ask(question)
    await p.close()
    print(reply)
    print(f"\n[{time.time() - t0:.1f}s wall, model {model_ms} ms]", file=sys.stderr)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--dry":
        asyncio.run(dry(" ".join(sys.argv[2:])))
    else:
        asyncio.run(Loop().run())
