#!/usr/bin/env python3
"""Emit a compact authoring pack for one section: every endpoint with its class,
backend, and generated CLI command — plus grepped payload keys for the reads.
Usage: section_pack.py <Section-Stem>"""
import os, re, sys, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = os.path.join(ROOT, "captures")
CLI = os.path.join(ROOT, "cli")
JS = os.path.join(CAP, "js")

USE = {'Dashboard':'dashboard','Employee-Management':'employee','Attendance':'attendance',
 'Leave-Management':'leave','Payouts':'payouts','Approvals':'approvals','Accounts-Taxes':'accounts',
 'Reports':'reports','Recruit-ATS':'recruit','Masters-Config':'masters','Org-User-Management':'org',
 'Broadcast-Visitor-Help':'broadcast','Contract-Labour-Inventory':'contract','Training-Performance':'training'}

BACKENDS = [("business","https://business.tankhapay.com/api/"),("mobapi","https://mobapi.tankhapay.com/api/"),
 ("tnd","https://tnd.tankhapay.com/api/"),("tpPay","https://mobapi.tankhapay.com/")]

def backend_of(u):
    for k,b in BACKENDS:
        if u.startswith(b): return k, u[len(b):]
    return "?", u

def lastseg(u): return u.split('?')[0].rstrip('/').split('/')[-1]

def payload_keys(seg):
    """Grep the corpus for a call site of this action and pull object-literal keys."""
    try:
        out = subprocess.run(["grep","-rhoE", seg+r"\(\{[^}]{0,240}", JS],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return ""
    if not out:
        return ""
    line = out.splitlines()[0]
    keys = re.findall(r'([A-Za-z_]\w*)\s*:', line.split("({",1)[-1])
    seen, uniq = set(), []
    for k in keys:
        if k not in seen and k not in ("this","function"):
            seen.add(k); uniq.append(k)
    return ",".join(uniq[:10])

def main():
    stem = sys.argv[1]
    use = USE[stem]
    rows = [l.rstrip("\n").split("\t") for l in open(os.path.join(CAP,"sections",stem+".tsv")) if l.strip()]
    recl = {}
    for l in open(os.path.join(CAP,"reclassified-writes.tsv")):
        p = l.rstrip("\n").split("\t"); recl[p[0]] = p[1] if len(p)>1 else "write"
    man = open(os.path.join(CLI,"wired_manifest.go")).read()
    url2cmd = dict(re.findall(r'Cmd: "([^"]+)", Backend: "[^"]+", Path: "[^"]+", URL: "([^"]+)"', man))
    url2cmd = {u:c for c,u in url2cmd.items()}

    reads, writes, unknown = [], [], []
    for cls, url in [(r[0], r[-1]) for r in rows]:
        be, rel = backend_of(url)
        if url in recl:
            writes.append((rel, be, "RECLASSIFIED read→write: "+recl[url]))
        elif cls == "READ":
            reads.append((url2cmd.get(url,"?"), be, rel))
        elif cls == "WRITE":
            writes.append((rel, be, "write"))
        else:
            unknown.append((rel, be))

    print(f"SECTION {stem}  use={use}  reads={len(reads)} writes={len(writes)} unknown={len(unknown)}")
    print("--- READ (wired commands) : cmd | backend | relpath | payloadKeys ---")
    for cmd, be, rel in sorted(reads):
        print(f"{cmd}\t{be}\t{rel}\t{payload_keys(lastseg(rel))}")
    print("--- WRITE / out-of-scope : relpath | backend | why ---")
    for rel, be, why in sorted(writes):
        print(f"{rel}\t{be}\t{why}")
    if unknown:
        print("--- UNKNOWN (not wired) : relpath | backend ---")
        for rel, be in sorted(unknown):
            print(f"{rel}\t{be}")

if __name__ == "__main__":
    main()
