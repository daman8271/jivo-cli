#!/usr/bin/env python3
"""accounts-data-serve.py — loopback static server for the accounts-board data.

Why this exists: the Vercel free plan allows 100 deployments per rolling 24h
across the whole account, and on 2026-08-24 the 2-minute live-refresh loop
burned through it by mid-morning (the v2 board sat 8.5 hours stale while the
site answered 200). So the DATA no longer rides Vercel deployments at all:
live-refresh.sh drops each verified build into /srv/accounts-data, this server
hands it to Traefik on 127.0.0.1:7799, and both Vercel sites carry a rewrite
(/data.json and /data/*) that proxies here. Vercel is now touched only when
the HTML itself changes.

Runs as systemd unit `accounts-data.service` (loopback only, behind the
Traefik route in /docker/traefik/dynamic/jivo-accounts-data.yml). The board
data is public by Daman's explicit call (2026-08-21), so the route carries no
auth — the same figures are on the public dashboards themselves.

Only .json/.jsonl under the root are served: no listings, no other types, and
paths are confined to ROOT. Cache-Control: no-store keeps Vercel's edge from
pinning a stale copy; gzip because v1's data.json is ~9 MB raw and ~600 KB
compressed.
"""
import gzip
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.environ.get("ACCOUNTS_DATA_ROOT", "/srv/accounts-data")
TYPES = {
    ".json": "application/json; charset=utf-8",
    ".jsonl": "application/x-ndjson; charset=utf-8",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "accounts-data/1"
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def do_GET(self):
        self._serve(send_body=True)

    def do_HEAD(self):
        self._serve(send_body=False)

    def _refuse(self, code):
        self.send_response(code)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _serve(self, send_body):
        path = self.path.split("?", 1)[0]
        full = os.path.normpath(os.path.join(ROOT, path.lstrip("/")))
        ext = os.path.splitext(full)[1]
        if not full.startswith(ROOT + os.sep) or ext not in TYPES:
            return self._refuse(404)
        try:
            with open(full, "rb") as f:
                data = f.read()
        except OSError:
            return self._refuse(404)
        gz = "gzip" in self.headers.get("Accept-Encoding", "") and len(data) > 1024
        if gz:
            data = gzip.compress(data, 6)
        self.send_response(200)
        self.send_header("Content-Type", TYPES[ext])
        if gz:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        if send_body:
            self.wfile.write(data)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 7799
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
