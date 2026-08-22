#!/usr/bin/env python3
"""jivo-summond — the "Let's go" receiver.

An operator on any fleet box says "Let's go". Their box POSTs here. This daemon
authenticates the box, writes the request to an append-only audit log, and hands
it to a REAL interactive Claude session living in tmux on this VPS (see pool.py).
The answer comes back to them.

Deliberate design choices, because this endpoint can grant permissions:

  * Bearer token per DEVICE, compared with hmac.compare_digest. The token IS the
    device's identity; there is no "trust the X-Jivo-Device header" path.
  * The operator's free text NEVER reaches a shell. Only a 32-char hex id is
    typed into tmux. See pool.py.
  * The agent cannot run arbitrary commands against fleet boxes. It can only call
    `grantctl <grant> <box>`, and grantctl validates both against policy.json.
    So even a fully prompt-injected agent is confined to the catalogue.
  * Every request and every outcome is appended to audit.jsonl and fsync'd before
    the response is returned. No silent grants.
  * Tokens are never logged; only a short fingerprint.

Stdlib only, matching the existing jivo-webhook service on this box.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pool import SessionPool, new_id  # noqa: E402

ROOT = Path(os.environ.get("SUMMON_ROOT", "/opt/jivo-summon"))
TOKENS_PATH = ROOT / "tokens.json"
POLICY_PATH = ROOT / "policy.json"
AUDIT_PATH = Path(os.environ.get("SUMMON_AUDIT", ROOT / "audit.jsonl"))

BIND_HOST = os.environ.get("SUMMON_BIND", "127.0.0.1")
BIND_PORT = int(os.environ.get("SUMMON_PORT", "8710"))
POOL_SIZE = int(os.environ.get("SUMMON_POOL_SIZE", "3"))

MAX_BODY = 64 * 1024
RATE_WINDOW_S = 60
RATE_MAX = 12  # per device per minute

VERSION = "1.0.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s jivo-summond %(levelname)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger("summond")

_audit_lock = threading.Lock()
_rate_lock = threading.Lock()
_rate: dict[str, list[float]] = {}

POOL = SessionPool(size=POOL_SIZE)


# ------------------------------------------------------------------ helpers


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fingerprint(token: str) -> str:
    """A loggable stand-in for a token. Never log the token itself."""
    return hashlib.sha256(token.encode()).hexdigest()[:12]


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def audit(record: dict) -> None:
    """Append-only, fsync'd. A grant that is not in here did not happen."""
    record = {"ts": now_iso(), **record}
    line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    with _audit_lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_PATH, "a", encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())


def authenticate(header: str | None) -> dict | None:
    """Bearer token -> device record, or None.

    Constant-time compare against every known token so a wrong token cannot be
    distinguished by timing from an unknown one.
    """
    if not header or not header.startswith("Bearer "):
        return None
    presented = header[len("Bearer "):].strip()
    if not presented:
        return None
    tokens = load_json(TOKENS_PATH, {})
    match = None
    for token, record in tokens.items():
        if hmac.compare_digest(token, presented):
            match = record
    if match is None:
        return None
    if match.get("disabled"):
        return None
    return {**match, "token_fp": fingerprint(presented)}


def rate_ok(device: str) -> bool:
    cutoff = time.time() - RATE_WINDOW_S
    with _rate_lock:
        hits = [t for t in _rate.get(device, []) if t > cutoff]
        if len(hits) >= RATE_MAX:
            _rate[device] = hits
            return False
        hits.append(time.time())
        _rate[device] = hits
        return True


# ------------------------------------------------------------------ handler


class Handler(BaseHTTPRequestHandler):
    server_version = f"jivo-summond/{VERSION}"

    def log_message(self, fmt, *args):  # quieter, and never logs bodies
        log.info("%s %s", self.address_string(), fmt % args)

    # -- plumbing

    def _wants_text(self) -> bool:
        """Does this client want a rendered answer instead of JSON?

        Several Windows fleet boxes have no working python — their python.exe is a
        Microsoft Store stub that prints "Python was not found" and exits 0 — so
        their client cannot parse JSON. They send Accept: text/plain and get the
        answer already rendered, with nothing to parse.
        """
        return "text/plain" in (self.headers.get("Accept") or "").lower()

    def _render(self, payload: dict) -> str:
        reply = payload.get("reply") or {}
        answer = reply.get("answer")
        if not answer:
            return (payload.get("error") or "no answer") + "\n"
        out = ["", answer, ""]
        for key, label in (("grants_applied", "granted"),
                           ("grants_refused", "refused"),
                           ("blocked_on", "still needs a human")):
            vals = [v for v in (reply.get(key) or []) if v]
            if vals:
                out.append(f"{label}:")
                out += [f"  - {v}" for v in vals]
                out.append("")
        if reply.get("confidence") and reply["confidence"] != "high":
            out.append(f"(confidence: {reply['confidence']})")
        out.append(f"summon {payload.get('id', '?')} via {payload.get('via', '?')}")
        return "\n".join(out) + "\n"

    def _send(self, code: int, payload: dict) -> None:
        if self._wants_text():
            body = self._render(payload).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                self.wfile.write(body)
            except BrokenPipeError:
                pass
            return
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def _read_body(self) -> dict | None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return None
        if length <= 0 or length > MAX_BODY:
            return None
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def _path(self) -> str:
        # Traefik strips the obfuscated prefix; be tolerant of a trailing slash.
        return "/" + self.path.split("?", 1)[0].strip("/")

    # -- routes

    def do_GET(self):  # noqa: N802
        path = self._path()

        if path == "/healthz":
            # Unauthenticated on purpose: liveness only, no fleet detail.
            self._send(200, {"ok": True, "service": "jivo-summond", "version": VERSION})
            return

        caller = authenticate(self.headers.get("Authorization"))
        if caller is None:
            self._send(401, {"ok": False, "error": "unauthorized"})
            return

        if path == "/v1/status":
            self._send(200, {
                "ok": True,
                "version": VERSION,
                "sessions": POOL.status(),
                "policy_loaded": POLICY_PATH.exists(),
                "you": {"device": caller.get("device"), "operator": caller.get("operator")},
            })
            return

        if path == "/v1/audit":
            if "audit" not in caller.get("scopes", []):
                self._send(403, {"ok": False, "error": "scope 'audit' required"})
                return
            try:
                lines = AUDIT_PATH.read_text(encoding="utf-8").splitlines()[-200:]
            except OSError:
                lines = []
            self._send(200, {"ok": True, "entries": [json.loads(x) for x in lines if x.strip()]})
            return

        self._send(404, {"ok": False, "error": "no such route"})

    def do_POST(self):  # noqa: N802
        path = self._path()
        if path != "/v1/summon":
            self._send(404, {"ok": False, "error": "no such route"})
            return

        caller = authenticate(self.headers.get("Authorization"))
        if caller is None:
            audit({
                "event": "auth_failed",
                "peer": self.address_string(),
                "path": path,
            })
            self._send(401, {"ok": False, "error": "unauthorized"})
            return

        device = caller.get("device", "unknown")
        operator = caller.get("operator", "unknown")

        if not rate_ok(device):
            audit({"event": "rate_limited", "device": device, "operator": operator})
            self._send(429, {"ok": False, "error": "too many summons; wait a minute"})
            return

        body = self._read_body()
        if body is None:
            self._send(400, {"ok": False, "error": "bad or oversized JSON body"})
            return

        sid = new_id()
        request = {
            "id": sid,
            "received": now_iso(),
            # Identity comes from the TOKEN, never from a client-supplied header.
            "device": device,
            "operator": operator,
            "scopes": caller.get("scopes", []),
            "ssh_alias": caller.get("ssh_alias", ""),
            "os": str(body.get("os", ""))[:64],
            "cwd": str(body.get("cwd", ""))[:512],
            "say": str(body.get("say", "let's go"))[:256],
            # Free text. Untrusted. Never reaches a shell; only the agent reads it.
            "ask": str(body.get("ask", ""))[:8000],
            "peer": self.address_string(),
        }

        audit({
            "event": "summon_received",
            "id": sid,
            "device": device,
            "operator": operator,
            "token_fp": caller.get("token_fp"),
            "say": request["say"],
            "ask": request["ask"][:2000],
        })

        try:
            result = POOL.dispatch(request)
            if not result.get("ok") and result.get("retry"):
                log.warning("summon %s: session path failed (%s); falling back to one-shot",
                            sid, result.get("error"))
                audit({"event": "session_failed", "id": sid, "error": result.get("error")})
                result = POOL.fallback_oneshot(request)
        except Exception as exc:  # noqa: BLE001 - never 500 without an audit line
            log.exception("summon %s blew up", sid)
            audit({"event": "summon_error", "id": sid, "error": repr(exc)})
            self._send(500, {"ok": False, "id": sid, "error": "summon failed; see audit log"})
            return

        audit({
            "event": "summon_answered" if result.get("ok") else "summon_failed",
            "id": sid,
            "device": device,
            "operator": operator,
            "via": result.get("via"),
            "grants_applied": (result.get("reply") or {}).get("grants_applied", []),
            "error": result.get("error", ""),
        })

        self._send(200 if result.get("ok") else 503, {"ok": result.get("ok"), "id": sid, **result})


def main() -> int:
    for d in ("queue", "replies", "workspace", "state"):
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    if not TOKENS_PATH.exists():
        log.error("no tokens file at %s — every request will 401", TOKENS_PATH)
    # Bind FIRST. Warming three tmux sessions takes ~6s each, and doing it before
    # the bind left the port dead for 20s after systemd already reported the unit
    # active — which reads as a failed deploy and races any health check.
    srv = ThreadingHTTPServer((BIND_HOST, BIND_PORT), Handler)
    srv.daemon_threads = True
    log.info("listening on %s:%s  pool=%d  audit=%s",
             BIND_HOST, BIND_PORT, POOL_SIZE, AUDIT_PATH)

    # Warm the pool in the background so the first summon of the day does not pay
    # for session startup, while /healthz answers immediately.
    def warm() -> None:
        for slot in POOL.slots:
            try:
                POOL.ensure(slot)
                log.info("warmed %s", slot.name)
            except Exception:  # noqa: BLE001
                log.exception("could not warm %s", slot.name)

    threading.Thread(target=warm, name="warm-pool", daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
