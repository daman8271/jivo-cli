#!/usr/bin/env python3
"""
board_server.py — serves the approval board's JSON to the browser.

Read-only, loopback-only, behind Traefik. The Vercel page holds the UI and
nothing else; every number on screen comes from here. That split exists because
the board refreshes every minute and Vercel's free plan allows 100 deploys a day
— baking the data into the page would blow that by mid-morning.

Routes:  /board.json  /history.jsonl  /healthz
"""
import json, os, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone, timedelta

IST   = timezone(timedelta(hours=5, minutes=30))
ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state")
ADDR  = ("127.0.0.1", int(os.environ.get("APPROVAL_BOARD_PORT", "8798")))
# If the builder has not written in this long, say so out loud rather than
# serving a stale board as though it were live.
STALE_AFTER_S = 300


def _send(h, code, body, ctype="application/json; charset=utf-8"):
    raw = body if isinstance(body, bytes) else body.encode("utf-8")
    h.send_response(code)
    h.send_header("Content-Type", ctype)
    h.send_header("Content-Length", str(len(raw)))
    h.send_header("Cache-Control", "no-store, must-revalidate")
    h.send_header("Access-Control-Allow-Origin", "*")
    h.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    h.end_headers()
    if h.command != "HEAD":
        h.wfile.write(raw)


def _age_seconds(path):
    try:
        return (datetime.now(IST) - datetime.fromtimestamp(os.path.getmtime(path), IST)).total_seconds()
    except OSError:
        return None


class Handler(BaseHTTPRequestHandler):
    server_version = "jivo-approval-board"

    def do_OPTIONS(self):
        _send(self, 204, b"")

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        board = os.path.join(STATE, "board.json")

        if path in ("/", "/board.json"):
            try:
                with open(board, "rb") as fh:
                    return _send(self, 200, fh.read())
            except OSError:
                return _send(self, 503, json.dumps({"error": "board.json not built yet"}))

        if path == "/history.jsonl":
            try:
                with open(os.path.join(STATE, "history.jsonl"), "rb") as fh:
                    return _send(self, 200, fh.read(), "application/x-ndjson; charset=utf-8")
            except OSError:
                return _send(self, 200, b"", "application/x-ndjson; charset=utf-8")

        if path == "/healthz":
            age = _age_seconds(board)
            ok = age is not None and age < STALE_AFTER_S
            return _send(self, 200 if ok else 503, json.dumps({
                "ok": ok,
                "board_age_seconds": None if age is None else round(age, 1),
                "stale_after_seconds": STALE_AFTER_S,
                "now": datetime.now(IST).isoformat(),
            }))

        return _send(self, 404, json.dumps({"error": "not found"}))

    def log_message(self, fmt, *a):      # journald already stamps the time
        sys.stderr.write("%s\n" % (fmt % a))


if __name__ == "__main__":
    ThreadingHTTPServer(ADDR, Handler).serve_forever()
