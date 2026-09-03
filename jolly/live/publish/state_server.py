#!/usr/bin/env python3
"""Mark 3 state publisher — serves live/state/*.json read-only on 127.0.0.1.

Traefik fronts it over HTTPS (see mark3-state.traefik.yml). It serves ONLY
*.json files from one directory, adds CORS so the Mark 3 site can fetch
client-side, and Cache-Control: no-store so nothing stale is ever cached.
No listing, no other paths, no writes — GET/HEAD only.
"""
import http.server, os, sys, json, datetime

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "state")
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8793

class H(http.server.BaseHTTPRequestHandler):
    server_version = "mark3-state/1"
    def _hdr(self, code, ctype="application/json", length=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        if length is not None: self.send_header("Content-Length", str(length))
        self.end_headers()
    def _path(self):
        # state.json at the root, plus the Phase-4 plan files under plan/ and plan/days/.
        # Still *.json only, no dotfiles, no empty segments, never outside ROOT.
        name = self.path.split("?", 1)[0].lstrip("/") or "state.json"
        parts = name.split("/")
        if not name.endswith(".json") or any(seg == "" or seg.startswith(".") for seg in parts): return None
        if len(parts) == 2 and parts[0] != "plan": return None
        if len(parts) == 3 and (parts[0], parts[1]) != ("plan", "days"): return None
        if len(parts) > 3: return None
        p = os.path.normpath(os.path.join(ROOT, *parts))
        if not p.startswith(ROOT + os.sep): return None
        return p if os.path.isfile(p) else None
    def do_OPTIONS(self): self._hdr(204, length=0)
    def do_HEAD(self):
        p = self._path()
        if not p: return self._hdr(404, length=0)
        self._hdr(200, length=os.path.getsize(p))
    def do_GET(self):
        if self.path.split("?",1)[0] in ("/healthz", "/"):
            body = json.dumps({"ok": True, "root": ROOT, "now": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                               "files": sorted(f for f in os.listdir(ROOT) if f.endswith(".json")),
                               "plan_files": len([f for f in os.listdir(os.path.join(ROOT,"plan")) if f.endswith(".json")]) if os.path.isdir(os.path.join(ROOT,"plan")) else 0}).encode()
            self._hdr(200, length=len(body)); self.wfile.write(body); return
        p = self._path()
        if not p:
            body = b'{"error":"not found"}'; self._hdr(404, length=len(body)); self.wfile.write(body); return
        with open(p, "rb") as f: body = f.read()
        self._hdr(200, length=len(body)); self.wfile.write(body)
    def log_message(self, *a): pass  # quiet; Traefik logs the edge

if __name__ == "__main__":
    os.makedirs(ROOT, exist_ok=True)
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
