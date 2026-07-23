#!/usr/bin/env python3
"""Read-only endpoint x company sweep for factory.jivo.in.

For every candidate GET endpoint (research/endpoints.txt), probe all three
Company-Code values with page_size=1 and record status / kind / count / body
hash per company. Output: research/company-matrix.tsv.

READ-ONLY LAW: GET requests only. Auth/action endpoints are skipped entirely
(even a GET on /accounts/logout/ is not worth the risk). Token is read from
the file given by JIVO_FACTORY_TOKEN_FILE — never stored here.
"""

import concurrent.futures
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://factory.jivo.in/api/v1"
COMPANIES = ["JIVO_MART", "JIVO_OIL", "JIVO_BEVERAGES"]
SKIP_SUBSTR = [
    "/login",
    "/logout",
    "/change-password",
    "/token/refresh",
    "/register",
    "/unregister",
    "/mark-read",
    "/send",
    "/test",
    "/refresh/",  # sales-planning-requirement/refresh/ triggers a rebuild upstream
    "/generate",
    "/create",
    "/post",
    "/submit",
    "/scan/",
    "/print/bulk",
]

HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.environ.get("JIVO_FACTORY_TOKEN_FILE")
if not TOKEN_FILE or not os.path.exists(TOKEN_FILE):
    sys.exit("JIVO_FACTORY_TOKEN_FILE not set or missing")
TOKEN = open(TOKEN_FILE).read().strip()


def probe(path, company):
    url = f"{API}{path}"
    sep = "&" if "?" in url else "?"
    req = urllib.request.Request(
        url + f"{sep}page_size=1",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Company-Code": company,
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read()
            status = r.status
    except urllib.error.HTTPError as e:
        return {"status": e.code, "kind": "-", "count": "-", "md5": "-"}
    except Exception as e:
        return {
            "status": f"ERR:{type(e).__name__}",
            "kind": "-",
            "count": "-",
            "md5": "-",
        }
    md5 = hashlib.md5(body).hexdigest()[:10]
    kind, count = "raw", "-"
    try:
        data = json.loads(body)
        if isinstance(data, dict):
            if "count" in data and "results" in data:
                kind, count = "paginated_list", data["count"]
            else:
                kind, count = "object", "-"
        elif isinstance(data, list):
            kind, count = "list", f">={len(data)}"
    except Exception:
        pass
    return {"status": status, "kind": kind, "count": count, "md5": md5}


def sweep_endpoint(path):
    row = {"path": path}
    for c in COMPANIES:
        row[c] = probe(path, c)
        time.sleep(0.15)
    md5s = [row[c]["md5"] for c in COMPANIES]
    all200 = all(row[c]["status"] == 200 for c in COMPANIES)
    row["shared"] = (
        "SHARED" if (all200 and len(set(md5s)) == 1) else ("scoped" if all200 else "-")
    )
    return row


def main():
    eps = [
        line.strip()
        for line in open(os.path.join(HERE, "endpoints.txt"))
        if line.strip()
    ]
    eps = [e for e in eps if not any(s in e for s in SKIP_SUBSTR)]
    print(f"sweeping {len(eps)} endpoints x {len(COMPANIES)} companies (GET only)")
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for i, row in enumerate(ex.map(sweep_endpoint, eps), 1):
            rows.append(row)
            if i % 25 == 0:
                print(f"  {i}/{len(eps)}")
    rows.sort(key=lambda r: r["path"])
    out = os.path.join(HERE, "company-matrix.tsv")
    with open(out, "w") as f:
        f.write(
            "path\tshared\t"
            + "\t".join(f"{c}_status\t{c}_kind\t{c}_count" for c in COMPANIES)
            + "\n"
        )
        for r in rows:
            cells = []
            for c in COMPANIES:
                p = r[c]
                cells += [str(p["status"]), p["kind"], str(p["count"])]
            f.write(f"{r['path']}\t{r['shared']}\t" + "\t".join(cells) + "\n")
    live_any = sum(1 for r in rows if any(r[c]["status"] == 200 for c in COMPANIES))
    shared = sum(1 for r in rows if r["shared"] == "SHARED")
    print(
        f"done → {out}\n{live_any}/{len(rows)} endpoints live for >=1 company; {shared} SHARED across all 3"
    )


if __name__ == "__main__":
    main()
