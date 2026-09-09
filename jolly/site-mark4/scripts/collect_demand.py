"""Independent CLI-only demand refresh; never writes the Mark3 collector/cache.

Example: python3 collect_demand.py --raw-dir PRIVATE --out STATE/demand-supplement.json
  --ecom-bin CLI --ecom-config CONFIG --oms-bin CLI --oms-config CONFIG
  --oms-frontier 3168

Full numeric OMS discovery is deliberate: list/status filters are account-scoped.
A daily full scan backs up each cycle's all-user headers and active detail reads.
On any failure the output retains old data with its ORIGINAL data.asOf and ok:false.
"""
from __future__ import annotations
import argparse
import base64
import re
import collections
import concurrent.futures
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time
from demand_source import normalize_directory, TERMINAL

def now(): return dt.datetime.now(dt.timezone.utc).isoformat()

def atomic(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False))
    os.chmod(temporary, 0o600)
    temporary.replace(path)

def cli(binary, args, config):
    try:
        env = os.environ.copy()
        for key in ("OMS_TOKEN", "JIVO_ECOM_TOKEN"): env.pop(key, None)
        p = subprocess.run([binary, *args, "--config", config, "--json", "--no-input", "--no-cache", "--data-source", "live", "--timeout", "30s"], capture_output=True, text=True, timeout=35, env=env)
    except subprocess.TimeoutExpired: raise RuntimeError("Source read timed out") from None
    if p.returncode:
        if "HTTP 404" in p.stderr or "returned 404" in p.stderr: raise FileNotFoundError("Source ID absent")
        if "401" in p.stderr: raise RuntimeError("Source authentication expired")
        raise RuntimeError("Source CLI read failed")
    try: return json.loads(p.stdout)
    except ValueError: raise RuntimeError("Source returned unreadable JSON") from None

def renew_auth(a):
    if not a.auth_env: return
    values = {}
    for line in Path(a.auth_env).read_text().splitlines():
        if "=" not in line or line.lstrip().startswith("#"): continue
        key,value=line.split("=",1); values[key.strip()]=value.strip().strip("\"'")
    for binary,config,keys in ((a.ecom_bin,a.ecom_config,("JIVO_ECOM_EMAIL","JIVO_ECOM_PASSWORD")), (a.oms_bin,a.oms_config,("OMS_USERNAME","OMS_PASSWORD"))):
        text=Path(config).read_text(); match=re.search(r"(?m)^\s*(?:access_token|token)\s*=\s*[\"']([^\"']+)",text)
        try: expiry=json.loads(base64.urlsafe_b64decode(match[1].split(".")[1]+"==="))["exp"]
        except Exception: expiry=0
        if expiry-time.time()>600: continue
        if not all(values.get(k) for k in keys): raise RuntimeError("Independent source login credentials unavailable")
        env=os.environ.copy()
        for k in ("OMS_TOKEN","JIVO_ECOM_TOKEN"):env.pop(k,None)
        env.update({k:values[k] for k in keys})
        result=subprocess.run([binary,"auth","login","--config",config,"--json","--no-input"],env=env,capture_output=True,text=True,timeout=40)
        if result.returncode:raise RuntimeError("Independent source login renewal failed")

def ecom_pages(a, name, command, key):
    rows, count, seen = [], None, set()
    for page in range(100):
        body = cli(a.ecom_bin, command + ["--page", str(page), "--page-size", "1000"], a.ecom_config)
        result = body.get("results")
        if not isinstance(result, dict) or not isinstance(result.get(key), list): raise RuntimeError("Malformed paginated source")
        batch = result[key]
        if count is None: count = result.get("count")
        if not isinstance(count, int) or count < 0: raise RuntimeError("Source row count missing")
        fingerprint = json.dumps(batch, sort_keys=True)
        if batch and fingerprint in seen: raise RuntimeError("Source repeated a page")
        seen.add(fingerprint); rows.extend(batch)
        if len(rows) >= count:
            if len(rows) != count: raise RuntimeError("Source count does not reconcile")
            atomic(Path(a.raw_dir) / (name + "-rows.json"), rows)
            return {"feed": name, "rows": len(rows), "pages": page + 1, "asOf": now()}
        if not batch: raise RuntimeError("Source ended before declared count")
    raise RuntimeError("Source pagination cap reached")

def discover_oms(a):
    root = Path(a.raw_dir)
    existing = [int(p.stem[4:]) for p in root.glob("oms-[0-9]*.json")]
    frontier = max([a.oms_frontier, *existing])
    if frontier < 1: raise RuntimeError("Initial OMS known frontier required")
    started = now(); statuses = {}
    def one(i):
        for attempt in range(2):
            try:
                body = cli(a.oms_bin, ["orders", "detail", str(i)], a.oms_config)
                if not isinstance(body.get("results"), dict) or str(body["results"].get("id")) != str(i): raise RuntimeError("Order identity did not reconcile")
                atomic(root / f"oms-{i}.json", body)
                return i, "ok"
            except FileNotFoundError:
                (root / f"oms-{i}.json").unlink(missing_ok=True)
                return i, "missing"
            except RuntimeError as error:
                if "authentication" in str(error): return i, "auth_error"
                if attempt: return i, "error"
                time.sleep(.25)
        return i, "error"
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        statuses.update(pool.map(one, range(1, frontier + 1)))
        if any(v not in ("ok", "missing") for v in statuses.values()):
            complete = False
        else:
            # Consecutive absent IDs beyond highest existing one prove observed frontier.
            trailing = 0
            for i in range(frontier + 1, frontier + 1001):
                key, result = one(i); statuses[key] = result
                if result not in ("ok", "missing"): break
                trailing = trailing + 1 if result == "missing" else 0
                if trailing >= 12: break
            complete = trailing >= 12 and all(v in ("ok", "missing") for v in statuses.values())
    status = {"started": started, "checkedAt": now(), "through": max(statuses), "complete": complete,
              "counts": dict(collections.Counter(statuses.values())), "ids": statuses}
    atomic(root / "oms-discovery-status.json", status)
    if any(v == "auth_error" for v in statuses.values()): raise RuntimeError("Source authentication expired")
    return status

def refresh_headers(a):
    """All account-user header lists, then current nonterminal details only.

    Full numeric discovery remains a dated backstop. User responses are reduced
    immediately to IDs; no account passwords/phone/email are cached.
    """
    root = Path(a.raw_dir); started = now()
    raw_users = cli(a.oms_bin, ["account", "users"], a.oms_config).get("results", {})
    users = raw_users.get("data") if isinstance(raw_users, dict) else None
    if not isinstance(users, list) or not users: raise RuntimeError("OMS user scope unreadable")
    ids = {int(r["id"]) for r in users}; del users, raw_users
    for path in root.glob("oms-[0-9]*.json"):
        creator = json.loads(path.read_text()).get("results", {}).get("created_by")
        if isinstance(creator, int): ids.add(creator)
    atomic(root / "oms-user-ids.json", sorted(ids))
    raw_status = cli(a.oms_bin, ["orders", "status"], a.oms_config).get("results")
    if not isinstance(raw_status, list): raise RuntimeError("OMS statuses unreadable")
    states = {str(r["id"]):str(r["name"]).upper().replace(" ", "_") for r in raw_status}
    headers = {}
    def read_user(i):
        rows = cli(a.oms_bin, ["orders", "by-user", str(i)], a.oms_config).get("results")
        if not isinstance(rows, list): raise RuntimeError("OMS header list unreadable")
        result = {}
        for r in rows:
            if r.get("id") is None or str(r.get("status")) not in states: raise RuntimeError("OMS header identity/status unknown")
            result[str(r["id"])] = {"status":states[str(r["status"])], "created_at":r.get("created_at")}
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(read_user, sorted(ids)): headers.update(result)
    # Header union is authoritative observed scope; probe beyond its latest ID
    # to detect new records from creators absent from the current user catalog.
    highest = max([a.oms_frontier, *map(int, headers)])
    trailing = 0; frontier_errors = []
    for candidate in range(highest + 1, highest + 101):
        try:
            body = cli(a.oms_bin, ["orders", "detail", str(candidate)], a.oms_config)
            row = body.get("results")
            if not isinstance(row, dict) or row.get("id") != candidate: raise RuntimeError("OMS frontier identity unknown")
            atomic(root / f"oms-{candidate}.json", body)
            headers[str(candidate)] = {"status":str(row.get("status") or "UNKNOWN").upper(), "created_at":row.get("created_at")}
            trailing = 0
        except FileNotFoundError: trailing += 1
        except RuntimeError as error:
            if "authentication" in str(error): raise
            frontier_errors.append(candidate); trailing = 0
        if trailing == 12: break
    if trailing < 12 or frontier_errors: raise RuntimeError("OMS new-ID frontier incomplete")
    active = [int(i) for i,h in headers.items() if h["status"] not in TERMINAL]
    failed = []
    def read_detail(i):
        try:
            body = cli(a.oms_bin, ["orders", "detail", str(i)], a.oms_config)
            if not isinstance(body.get("results"), dict) or str(body["results"].get("id")) != str(i): raise RuntimeError("OMS detail identity unknown")
            atomic(root / f"oms-{i}.json", body)
            return None
        except RuntimeError as error:
            if "authentication" in str(error): raise
            return str(i)
        except FileNotFoundError: return str(i)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        failed = [x for x in pool.map(read_detail, active) if x]
    snapshot = {"asOf":started, "checkedAt":now(), "complete":True, "userCount":len(ids), "orders":headers,
                "frontierThrough":candidate, "frontierAbsentTail":trailing, "activeDetailErrors":failed, "headerCount":len(headers), "activeCount":len(active), "highestHeaderId":max(map(int, headers)) if headers else None}
    atomic(root / "oms-header-snapshot.json", snapshot)
    return snapshot

def refresh_planner_identity(a):
    path = Path(a.planner_inputs)
    source = json.loads(path.read_text())
    if not isinstance(source.get("items"),dict) or not isinstance(source.get("plan"),list): raise RuntimeError("Planner identity source malformed")
    items = {str(code):{"name":str(row.get("name") or "")} for code,row in source["items"].items() if str(code).startswith("FG") and isinstance(row,dict)}
    for row in source["plan"]:
        if row.get("code"):
            items[str(row["code"])]={"name":str(row.get("sku") or ""),"packLitres":row.get("litres_per_piece")}
    meta=source.get("meta",{})
    stamp=meta.get("state_collected_at") or meta.get("frozen") or dt.datetime.fromtimestamp(path.stat().st_mtime,dt.timezone.utc).isoformat()
    atomic(Path(a.raw_dir)/"planner-identity.json",{"asOf":stamp,"source":"Original live planner identity input; inherited BOM separately checked by engine","items":items})

def main():
    p = argparse.ArgumentParser()
    for field in ("raw-dir", "out", "ecom-bin", "ecom-config", "oms-bin", "oms-config"): p.add_argument("--" + field, required=True)
    p.add_argument("--oms-frontier", type=int, default=0)
    p.add_argument("--planner-inputs", default="/root/jivo-courier/jolly/sim/live-inputs.json")
    p.add_argument("--full-scan-hours", type=float, default=24)
    p.add_argument("--auth-env", help="Private KEY=VALUE file for isolated CLI login renewal")
    p.add_argument("--reuse-discovery", action="store_true", help="Normalize an existing verified full discovery; intended for initial fixture compilation, not scheduled refresh")
    a = p.parse_args(); os.umask(0o077); root = Path(a.raw_dir); root.mkdir(parents=True, exist_ok=True)
    output = Path(a.out); lock = open(str(output) + ".lock", "w") if output.parent.exists() else None
    if lock is None:
        output.parent.mkdir(parents=True, exist_ok=True); lock = open(str(output) + ".lock", "w")
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: print('{"ok":false,"error":"Demand refresh already running"}'); return 75
    attempt = now()
    try:
        if not a.reuse_discovery:
            renew_auth(a)
            commands = [("amazon", ["reports", "amazon-po", "--po-status", "PENDING"], "results"),
                        ("qcomm", ["tables", "data", "--table", "master_po", "--column-filters", '[{"column":"open_close","values":["OPEN"]}]'], "data"),
                        ("products", ["master", "products"], "results")]
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
                source_reads = list(pool.map(lambda row: ecom_pages(a, *row), commands))
            atomic(root / "read-status.json", {"asOf": min(x["asOf"] for x in source_reads), "sources": source_reads})
            prior_scan = json.loads((root / "oms-discovery-status.json").read_text()) if (root / "oms-discovery-status.json").exists() else {}
            last_scan = dt.datetime.fromisoformat(prior_scan.get("checkedAt", "1970-01-01T00:00:00+00:00"))
            if (dt.datetime.now(dt.timezone.utc) - last_scan).total_seconds() >= a.full_scan_hours * 3600:
                discover_oms(a)
            refresh_headers(a)
        refresh_planner_identity(a)
        data = normalize_directory(root)
        complete = data["demandBook"]["coverage"] == "complete"
        atomic(output, {"asOf": data["asOf"], "attemptedAt": attempt, "ok": complete, "error": None if complete else "Fresh measured subtotal; some active OMS details could not be read.", "data": data})
        print(json.dumps({"ok": complete, "refreshed": True, "coverage": data["demandBook"]["coverage"], "dataAsOf": data["asOf"], "orders": len(data["orders"]), "onlineGross": data["demandBook"]["online"]["grossOpenLitres"], "tradeGross": data["demandBook"]["trade"]["grossOpenLitres"]}))
        return 0
    except Exception as error:
        prior = json.loads(output.read_text()) if output.exists() else {}
        # Never publish credentials, raw stderr, customer names, or exception internals.
        result = {"asOf": prior.get("data", {}).get("asOf") if isinstance(prior.get("data"), dict) else None, "attemptedAt": attempt, "ok": False, "error": "Independent demand refresh failed; last valid source data retained."}
        if isinstance(prior.get("data"), dict): result["data"] = prior["data"]
        atomic(output, result)
        print(json.dumps({"ok": False, "retained": "data" in result, "errorType": type(error).__name__}))
        return 1

if __name__ == "__main__": raise SystemExit(main())
