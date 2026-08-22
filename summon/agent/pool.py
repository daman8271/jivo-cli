#!/usr/bin/env python3
"""Session pool for the JIVO summon agent.

The summon agent is a REAL interactive Claude Code session, not a headless
one-shot. Each pool slot is a long-lived `claude` running inside its own tmux
session on the VPS, so it keeps context between summons, can be attached to by
a human (`tmux attach -t jivo-summon-1`), and keeps its prompt cache warm.

The request/reply channel is deliberately NOT screen-scraped. Scraping a TUI is
fragile and, worse, injecting an operator's free text into `tmux send-keys` is a
shell-injection hole. Instead:

    receiver  ->  writes queue/<id>.json          (the request, as data)
    receiver  ->  send-keys "summon <id>"          (id is a uuid4 hex, nothing else)
    agent     ->  writes replies/<id>.json         (the answer, as data)
    receiver  ->  polls for that file

So the only thing that ever reaches the shell is a 32-char hex id. The pane
exists purely so a human can watch and take over.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(os.environ.get("SUMMON_ROOT", "/opt/jivo-summon"))
QUEUE = ROOT / "queue"
REPLIES = ROOT / "replies"
WORKSPACE = ROOT / "workspace"
STATE = ROOT / "state"

SESSION_PREFIX = "jivo-summon"
ID_RE = re.compile(r"^[0-9a-f]{32}$")

# A summon that has not produced a reply file in this long is treated as wedged.
REPLY_TIMEOUT_S = int(os.environ.get("SUMMON_REPLY_TIMEOUT", "420"))
POLL_INTERVAL_S = 0.4


def _run(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, capture_output=True, text=True, timeout=timeout, check=False
    )


def new_id() -> str:
    return uuid.uuid4().hex


@dataclass
class Slot:
    index: int
    name: str
    lock: threading.Lock

    @property
    def tmux_target(self) -> str:
        # window 0, pane 0 of the session
        return f"{self.name}:0.0"


class SessionPool:
    """A fixed pool of tmux-hosted interactive Claude sessions."""

    def __init__(self, size: int = 3):
        self.size = size
        self.slots = [
            Slot(i, f"{SESSION_PREFIX}-{i}", threading.Lock())
            for i in range(1, size + 1)
        ]
        for d in (QUEUE, REPLIES, WORKSPACE, STATE):
            d.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- tmux

    def _session_exists(self, slot: Slot) -> bool:
        return _run(["tmux", "has-session", "-t", slot.name]).returncode == 0

    def _pane_pid_alive(self, slot: Slot) -> bool:
        cp = _run(
            ["tmux", "list-panes", "-t", slot.name, "-F", "#{pane_dead}"]
        )
        if cp.returncode != 0:
            return False
        # every pane must report not-dead
        vals = [v.strip() for v in cp.stdout.splitlines() if v.strip()]
        return bool(vals) and all(v == "0" for v in vals)

    def ensure(self, slot: Slot) -> bool:
        """Make sure this slot has a live interactive claude session."""
        if self._session_exists(slot) and self._pane_pid_alive(slot):
            return True
        self.recycle(slot)
        return self._session_exists(slot)

    def recycle(self, slot: Slot) -> None:
        """Tear down and restart one slot's session."""
        _run(["tmux", "kill-session", "-t", slot.name])
        # A real headed session: interactive `claude`, inside the summon
        # workspace, whose .claude/settings.json allowlists exactly the vetted
        # commands. Root cannot use --dangerously-skip-permissions, so the
        # allowlist is what makes it able to act without a human at the keyboard.
        cmd = (
            f"cd {WORKSPACE} && exec claude --permission-mode acceptEdits"
        )
        _run(
            [
                "tmux",
                "new-session",
                "-d",
                "-s",
                slot.name,
                "-x",
                "220",
                "-y",
                "50",
                "bash",
                "-lc",
                cmd,
            ]
        )
        # Give the TUI a moment to draw before anything is typed at it.
        time.sleep(float(os.environ.get("SUMMON_BOOT_WAIT", "6")))

    def status(self) -> list[dict]:
        out = []
        for s in self.slots:
            out.append(
                {
                    "slot": s.index,
                    "session": s.name,
                    "alive": self._session_exists(s) and self._pane_pid_alive(s),
                    "busy": s.lock.locked(),
                    "attach": f"tmux attach -t {s.name}",
                }
            )
        return out

    # ------------------------------------------------------------- dispatch

    def acquire(self, wait_s: float = 30.0) -> Slot | None:
        """Take the first free slot, waiting briefly if all are busy."""
        deadline = time.time() + wait_s
        while True:
            for s in self.slots:
                if s.lock.acquire(blocking=False):
                    return s
            if time.time() >= deadline:
                return None
            time.sleep(0.25)

    def dispatch(self, request: dict, timeout_s: int = REPLY_TIMEOUT_S) -> dict:
        """Hand one summon to a live session and wait for its reply file.

        Returns a dict with at least {ok, via, reply|error}.
        """
        sid = request["id"]
        if not ID_RE.match(sid):
            raise ValueError("bad summon id")

        qpath = QUEUE / f"{sid}.json"
        rpath = REPLIES / f"{sid}.json"
        qpath.write_text(json.dumps(request, indent=2), encoding="utf-8")

        slot = self.acquire()
        if slot is None:
            return {
                "ok": False,
                "via": "none",
                "error": "all sessions busy",
                "retry": True,
            }
        try:
            if not self.ensure(slot):
                return {
                    "ok": False,
                    "via": "session",
                    "error": f"could not start session {slot.name}",
                }

            # The ONLY thing that reaches the shell is the hex id.
            _run(["tmux", "send-keys", "-t", slot.tmux_target, f"summon {sid}"])
            _run(["tmux", "send-keys", "-t", slot.tmux_target, "Enter"])

            deadline = time.time() + timeout_s
            while time.time() < deadline:
                if rpath.exists():
                    try:
                        reply = json.loads(rpath.read_text(encoding="utf-8"))
                    except json.JSONDecodeError:
                        time.sleep(POLL_INTERVAL_S)
                        continue
                    return {
                        "ok": True,
                        "via": f"session:{slot.name}",
                        "reply": reply,
                    }
                time.sleep(POLL_INTERVAL_S)

            # Wedged. Capture the pane for a human to read, then recycle it so
            # the next summon is not handed the same stuck session.
            pane = _run(
                ["tmux", "capture-pane", "-p", "-t", slot.tmux_target, "-S", "-120"]
            ).stdout
            (STATE / f"wedged-{sid}.txt").write_text(pane, encoding="utf-8")
            self.recycle(slot)
            return {
                "ok": False,
                "via": f"session:{slot.name}",
                "error": f"no reply within {timeout_s}s; session recycled",
                "pane_tail": pane[-2000:],
                "retry": True,
            }
        finally:
            slot.lock.release()

    # ------------------------------------------------------------- fallback

    def fallback_oneshot(self, request: dict, timeout_s: int = 300) -> dict:
        """Headless one-shot, used ONLY when no live session could answer.

        This is strictly worse than a real session (no memory, no follow-up, no
        human able to watch) which is why it is the fallback and not the path.
        """
        sid = request["id"]
        prompt = (
            f"You are the JIVO summon agent, running as a one-shot fallback because "
            f"no interactive session was available.\n"
            f"Read {QUEUE / (sid + '.json')} and handle that summon exactly as "
            f"{WORKSPACE / 'CLAUDE.md'} instructs, including writing your reply to "
            f"{REPLIES / (sid + '.json')}."
        )
        cp = subprocess.run(
            ["claude", "-p", prompt, "--permission-mode", "acceptEdits"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            cwd=str(WORKSPACE),
            check=False,
        )
        rpath = REPLIES / f"{sid}.json"
        if rpath.exists():
            try:
                return {
                    "ok": True,
                    "via": "oneshot",
                    "reply": json.loads(rpath.read_text(encoding="utf-8")),
                }
            except json.JSONDecodeError:
                pass
        return {
            "ok": False,
            "via": "oneshot",
            "error": "fallback produced no parseable reply",
            "stdout_tail": (cp.stdout or "")[-2000:],
            "stderr_tail": (cp.stderr or "")[-1000:],
        }
