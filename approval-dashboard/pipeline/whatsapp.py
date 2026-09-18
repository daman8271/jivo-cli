#!/usr/bin/env python3
"""
whatsapp.py — the one way this board sends a WhatsApp.

It is DORMANT on purpose. As of 2026-09-18 neither WhatsApp route can send:
  * Wati (official API) — every endpoint answers
    {"ok":false,"error":true,"fullTrialEnd":true}; the trial has ended.
  * jwa (our linked device) — LOGGED_OUT since 2026-09-03 07:30; WhatsApp
    removed the device and a phone must scan a new QR.

Daman's call, 2026-09-18: build it ready, leave it dormant, and write down every
message it would have sent. The day somebody runs `jwa login` it starts sending
with no code change.

Recipients are a later phase (one Accounts group, and per-person). Until
state/recipients.json names somebody, this only ever logs.
"""
import json, os, subprocess
from datetime import datetime, timezone, timedelta

IST   = timezone(timedelta(hours=5, minutes=30))
ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state")
JWA   = os.environ.get("JWA_BIN", "/root/go/bin/jwa")


def recipients():
    """{"group": "<jid or number>", "people": {"USER07": "<number>", ...}}"""
    try:
        with open(os.path.join(STATE, "recipients.json"), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"group": None, "people": {}}


def linked():
    """True only if jwa is actually linked and could send right now."""
    try:
        p = subprocess.run([JWA, "doctor"], capture_output=True, text=True, timeout=20)
        return "linked      YES" in p.stdout or "linked\tYES" in p.stdout
    except (OSError, subprocess.SubprocessError):
        return False


def _log(entry):
    os.makedirs(STATE, exist_ok=True)
    with open(os.path.join(STATE, "alerts.log"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def send(to, text, why=""):
    """Send if we can; always write down what was meant to go. Never raises —
    an alarm that crashes the board is worse than no alarm."""
    entry = {"at": datetime.now(IST).isoformat(), "to": to, "why": why, "text": text}
    if not to:
        entry["sent"] = False
        entry["skipped"] = "no recipient configured"
        _log(entry)
        return False
    if not linked():
        entry["sent"] = False
        entry["skipped"] = "jwa not linked — needs `jwa login` (QR scan)"
        _log(entry)
        return False
    try:
        p = subprocess.run([JWA, "send", to, text], capture_output=True, text=True, timeout=60)
        entry["sent"] = p.returncode == 0
        if p.returncode != 0:
            entry["error"] = (p.stderr or p.stdout).strip()[:300]
    except (OSError, subprocess.SubprocessError) as exc:
        entry["sent"] = False
        entry["error"] = str(exc)[:300]
    _log(entry)
    return entry["sent"]
