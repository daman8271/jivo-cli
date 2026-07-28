#!/usr/bin/env python3
"""
Mock SAP Business One Service Layer — for END-TO-END testing of the `sapb1` CLI
WITHOUT the real (firewalled) server. Mimics the real /b1s/v1 contract:
 - POST /b1s/v1/Login   -> sets B1SESSION + ROUTEID cookies, 200 session JSON
 - GET  /b1s/v1/<Entity> -> OData collection {"odata.metadata","value",[odata.count]}
                            honours $top, $select, basic $filter, $inlinecount=allpages
 - POST /b1s/v1/Logout  -> 200
 - missing/È bad session -> 401 with the real SAP error shape

Run:  python3 serve.py --port 50000
Test: sapb1 --host 127.0.0.1 --port 50000 --company TESTDB --insecure doctor
Self-signed cert (cert.pem/key.pem) sits beside this file so the CLI's TLS +
--insecure path is exercised exactly like the real box.
"""
import argparse, json, os, ssl, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote

HERE = os.path.dirname(os.path.abspath(__file__))

# --- tiny but realistic fixture data (real field names from the SAP reference) ---
ORDERS = [
    {"DocEntry": 1, "DocNum": 1001, "DocDate": "2026-07-01", "CardCode": "C0001",
     "CardName": "Acme Retail Pvt Ltd", "DocTotal": 125400.0, "DocStatus": "O", "DocCurrency": "INR"},
    {"DocEntry": 2, "DocNum": 1002, "DocDate": "2026-07-03", "CardCode": "C0002",
     "CardName": "Bharat Foods", "DocTotal": 48200.0, "DocStatus": "O", "DocCurrency": "INR"},
    {"DocEntry": 3, "DocNum": 1003, "DocDate": "2026-06-20", "CardCode": "C0001",
     "CardName": "Acme Retail Pvt Ltd", "DocTotal": 9900.0, "DocStatus": "C", "DocCurrency": "INR"},
]
ITEMS = [
    {"ItemCode": "A1001", "ItemName": "Olive Oil 1L", "ItemsGroupCode": 100,
     "QuantityOnStock": 3.0, "Valid": "tYES"},
    {"ItemCode": "A1002", "ItemName": "Canola Oil 1L", "ItemsGroupCode": 100,
     "QuantityOnStock": 240.0, "Valid": "tYES"},
    {"ItemCode": "A1003", "ItemName": "Ghee 500g", "ItemsGroupCode": 101,
     "QuantityOnStock": 0.0, "Valid": "tYES"},
]
PARTNERS = [
    {"CardCode": "C0001", "CardName": "Acme Retail Pvt Ltd", "CardType": "cCustomer",
     "Phone1": "9800000001", "EmailAddress": "buy@acme.example", "CurrentAccountBalance": 125400.0},
    {"CardCode": "V0001", "CardName": "Nimbus Packaging", "CardType": "cSupplier",
     "Phone1": "9800000099", "EmailAddress": "sales@nimbus.example", "CurrentAccountBalance": -22000.0},
]
DATASETS = {"Orders": ORDERS, "Items": ITEMS, "BusinessPartners": PARTNERS}

VALID_SESSIONS = set()


def sap_error(code, msg):
    return json.dumps({"error": {"code": code, "message": {"lang": "en-us", "value": msg}}}).encode()


def apply_odata(rows, qs):
    rows = list(rows)
    # small $filter: supports "<Field> eq '<val>'" clauses, ANDed, with the
    # parentheses the real client adds e.g. (DocStatus eq 'O') and (CardCode eq 'C1')
    flt = qs.get("$filter", [None])[0]
    if flt:
        import re
        expr = unquote(flt).replace("(", " ").replace(")", " ")
        for clause in re.split(r"\s+and\s+", expr, flags=re.I):
            m = re.search(r"(\w+)\s+eq\s+'?([^']*?)'?\s*$", clause.strip())
            if m:
                f, v = m.group(1), m.group(2)
                rows = [r for r in rows if str(r.get(f)) == v]
    total = len(rows)
    top = qs.get("$top", [None])[0]
    if top and top.isdigit():
        rows = rows[: int(top)]
    sel = qs.get("$select", [None])[0]
    if sel:
        cols = [c.strip() for c in unquote(sel).split(",") if c.strip()]
        rows = [{c: r.get(c) for c in cols} for r in rows]
    return rows, total


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quieter
        pass

    def _send(self, code, body=b"", ctype="application/json", cookies=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for c in cookies or []:
            self.send_header("Set-Cookie", c)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _has_session(self):
        return "B1SESSION=" in (self.headers.get("Cookie") or "")

    def do_POST(self):
        path = urlparse(self.path).path
        n = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(n) if n else b""
        if path == "/b1s/v1/Login":
            try:
                body = json.loads(raw or b"{}")
            except Exception:
                return self._send(400, sap_error(-1, "Malformed JSON."))
            if not all(body.get(k) for k in ("CompanyDB", "UserName", "Password")):
                return self._send(400, sap_error(-1,
                    "'CompanyDB','UserName','Password' are all required."))
            sid = uuid.uuid4().hex
            VALID_SESSIONS.add(sid)
            payload = json.dumps({
                "odata.metadata": "https://mock/b1s/v1/$metadata#B1Sessions/@Element",
                "SessionId": sid, "Version": "1000201", "SessionTimeout": 30}).encode()
            return self._send(200, payload,
                              cookies=[f"B1SESSION={sid}; path=/; HttpOnly", "ROUTEID=.node0; path=/"])
        if path == "/b1s/v1/Logout":
            return self._send(204)
        return self._send(404, sap_error(-1, "Not found."))

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path
        if not path.startswith("/b1s/v1/"):
            return self._send(404, sap_error(-1, "Not found."))
        if not self._has_session():
            return self._send(401, sap_error(301, "Invalid session."))
        entity = path[len("/b1s/v1/"):].split("/")[0]
        qs = parse_qs(u.query, keep_blank_values=True)
        rows, total = apply_odata(DATASETS.get(entity, []), qs)
        out = {"odata.metadata": f"https://mock/b1s/v1/$metadata#{entity}", "value": rows}
        if qs.get("$inlinecount", [None])[0] == "allpages":
            out["odata.count"] = total
        return self._send(200, json.dumps(out).encode())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=50000)
    ap.add_argument("--host", default="127.0.0.1")
    a = ap.parse_args()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(os.path.join(HERE, "cert.pem"), os.path.join(HERE, "key.pem"))
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    print(f"mock SAP B1 Service Layer (TLS) on https://{a.host}:{a.port}/b1s/v1/  — Ctrl-C to stop")
    print("entities served: Orders, Items, BusinessPartners")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
