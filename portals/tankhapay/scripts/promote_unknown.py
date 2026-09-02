#!/usr/bin/env python3
"""Promote ONLY the UNKNOWN endpoints that are unambiguously reads (hand-vetted).
Everything else stays OUT — the golden read-only vow forbids wiring behavioral
writes/auth/dual-mode endpoints even on request. Rebuilds wired-reads.tsv
deterministically from the confirmed reads + this allowlist."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = os.path.join(ROOT, "captures")

# Hand-vetted READ-only UNKNOWN endpoints (by path relative to backend). Each is a
# clear list/get/query with no mutation semantics. Everything not here is held out.
READ_SAFE = {
    "TpHelpAndSupportApi/readTicketInternalDepartment",
    "recruit/allCandidates",
    "recruit/allTemplates",
    "recruit/allTemplateType",
    "recruit/allTemplateFields",
    "recruit/allTemplateFieldName",
    "recruit/letterTEmplateById",
    "mobile_api/employee/query/query_trail",
    "mobile_api/employee/query/tickets",
    "mobile_api/employee/query/type",
}

def rel(u):
    for b in ("https://business.tankhapay.com/api/","https://mobapi.tankhapay.com/api/",
              "https://tnd.tankhapay.com/api/","https://mobapi.tankhapay.com/"):
        if u.startswith(b): return u[len(b):]
    return u

rows = [l.rstrip("\n").split("\t") for l in open(os.path.join(CAP,"endpoints-raw.tsv")) if l.strip()]
reads = {r[-1].strip() for r in rows if r[0]=="READ"}
unknown = {r[-1].strip() for r in rows if r[0]=="UNKNOWN"}
reclassified = {l.split("\t")[0].strip() for l in open(os.path.join(CAP,"reclassified-writes.tsv")) if l.strip()}

base = reads - reclassified                          # the 287 confirmed reads
promoted = {u for u in unknown if rel(u) in READ_SAFE}
excluded = unknown - promoted

wired = sorted(base | promoted)
open(os.path.join(CAP,"wired-reads.tsv"),"w").write("\n".join(wired)+"\n")
open(os.path.join(CAP,"unknown-promoted.tsv"),"w").write("\n".join(sorted(promoted))+"\n")
open(os.path.join(CAP,"unknown-excluded.tsv"),"w").write(
    "\n".join(f"{u}\tHELD OUT (read-only vow): behavioral write / auth / dual-mode / unverified"
             for u in sorted(excluded))+"\n")

print(f"confirmed reads (base)   : {len(base)}")
print(f"promoted from UNKNOWN     : {len(promoted)}  (hand-vetted reads)")
print(f"UNKNOWN held out          : {len(excluded)}  (read-only vow)")
print(f"wired-reads.tsv total     : {len(wired)}")
print("--- promoted ---")
for u in sorted(promoted): print("  ", rel(u))
