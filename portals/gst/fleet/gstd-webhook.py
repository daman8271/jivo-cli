#!/usr/bin/env python3
"""gstd-webhook — "a device just came online, make sure GST is logged in".

Endpoints (all require  X-Gstd-Token: <token>  matching /root/gstd/state/token):
    POST /wake    -> runs `gstd ensure` in the background, 202 immediately
    GET  /status  -> current session + guard state, as text
    GET  /health  -> 200 "ok", no token needed (for a liveness probe)

BINDING: 127.0.0.1 by default, deliberately.

What is served here is the ability to drive logins on eight live GST
registrations, and the jars themselves are a bearer token to a portal that can
FILE STATUTORY RETURNS. Devices already have key-based SSH to this box, so they
can reach a loopback port through that and nothing needs to face the internet.
Set GSTD_BIND=0.0.0.0 only alongside TLS and a firewall rule, as a decision
somebody makes on purpose.

Note on direction: a webhook cannot be pushed TO a laptop that just woke up —
it is behind NAT with no stable address. The device has to make the call. So
the device-side hook (gst-sync) is what fires on network-up, and this is what
it calls.
"""
import http.server
import json
import os
import pathlib
import subprocess
import threading

GSTD = "/root/gstd/bin/gstd"
TOKEN_FILE = pathlib.Path("/root/gstd/state/token")
BIND = os.environ.get("GSTD_BIND", "127.0.0.1")
PORT = int(os.environ.get("GSTD_PORT", "7711"))

TOKEN = TOKEN_FILE.read_text().strip() if TOKEN_FILE.exists() else ""

# One ensure at a time. Two concurrent runs would race each other into the
# portal and could log the same registration in twice — which, on a
# one-session-per-username portal, means the second kicks the first off.
_lock = threading.Lock()
_running = threading.Event()


def _run_ensure():
    if not _lock.acquire(blocking=False):
        return
    try:
        _running.set()
        subprocess.run([GSTD, "ensure"], capture_output=True, timeout=900)
    except Exception:
        pass
    finally:
        _running.clear()
        _lock.release()


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "gstd/1.0"

    def _reply(self, code, body, ctype="text/plain; charset=utf-8"):
        raw = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _authed(self):
        if not TOKEN:
            self._reply(503, "no token configured on the server\n")
            return False
        if self.headers.get("X-Gstd-Token", "") != TOKEN:
            self._reply(403, "bad or missing X-Gstd-Token\n")
            return False
        return True

    def do_GET(self):
        if self.path == "/health":
            return self._reply(200, "ok\n")
        if self.path == "/status":
            if not self._authed():
                return
            out = subprocess.run([GSTD, "status"], capture_output=True, text=True, timeout=120)
            return self._reply(200, out.stdout + out.stderr)
        self._reply(404, "no such endpoint\n")

    def do_POST(self):
        if self.path != "/wake":
            return self._reply(404, "no such endpoint\n")
        if not self._authed():
            return
        if _running.is_set():
            return self._reply(
                202, json.dumps({"accepted": False, "reason": "an ensure is already running"}) + "\n",
                "application/json")
        threading.Thread(target=_run_ensure, daemon=True).start()
        self._reply(202, json.dumps({"accepted": True}) + "\n", "application/json")

    def log_message(self, fmt, *args):
        pass  # journald already timestamps; the real record is gstd.log


if __name__ == "__main__":
    srv = http.server.ThreadingHTTPServer((BIND, PORT), Handler)
    srv.serve_forever()
