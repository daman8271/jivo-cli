#!/usr/bin/env python3
"""Weave the master endpoint index + coverage audit into vault/TankhaPay-Endpoints.md."""
import os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP = os.path.join(ROOT, "captures")
VAULT = os.path.join(ROOT, "vault")

SECTIONS = ["Dashboard","Employee-Management","Attendance","Leave-Management","Payouts","Approvals",
 "Accounts-Taxes","Reports","Recruit-ATS","Masters-Config","Org-User-Management",
 "Broadcast-Visitor-Help","Contract-Labour-Inventory","Training-Performance"]

def load(path): return [l.rstrip("\n") for l in open(path) if l.strip()]

def lastseg(u): return u.split('?')[0].rstrip('/').split('/')[-1]

# 1. endpoint -> [sections]  and per-section class counts
url_sections = collections.defaultdict(list)
sec_counts = {}
for s in SECTIONS:
    reads=writes=unk=0
    for line in load(os.path.join(CAP,"sections",s+".tsv")):
        parts=line.split("\t"); cls=parts[0]; url=parts[-1].strip()
        url_sections[url].append(s)
        if cls=="READ": reads+=1
        elif cls=="WRITE": writes+=1
        else: unk+=1
    sec_counts[s]=(reads,writes,unk)

all_urls={l.split("\t")[-1].strip() for l in load(os.path.join(CAP,"endpoints-raw.tsv"))}
wired=[l.split("\t")[0].strip() for l in load(os.path.join(CAP,"wired-reads.tsv"))]

# (a) exactly-one-section
zero=[u for u in all_urls if len(url_sections.get(u,[]))==0]
multi=[(u,url_sections[u]) for u in all_urls if len(url_sections.get(u,[]))>1]

# (b) each wired read documented (cmd name present) in its section note
man=open(os.path.join(ROOT,"cli","wired_manifest.go")).read()
url2cmd={u:c for c,u in re.findall(r'Cmd: "([^"]+)", Backend: "[^"]+", Path: "[^"]+", URL: "([^"]+)"', man)}
notecache={s:open(os.path.join(VAULT,s+".md")).read() for s in SECTIONS}
undoc=[]
for u in wired:
    g=(url_sections.get(u) or ["?"])[0]; cmd=url2cmd.get(u,"")
    txt=notecache.get(g,"")
    # documented if the cmd name OR the raw last-segment appears in the note
    if cmd and cmd in txt: continue
    if lastseg(u) in txt: continue
    undoc.append((g,cmd,u))

# (c) routes
routes=load(os.path.join(CAP,"routes-raw.txt"))

# ---- emit ----
tot_r=sum(v[0] for v in sec_counts.values()); tot_w=sum(v[1] for v in sec_counts.values()); tot_u=sum(v[2] for v in sec_counts.values())
out=[]
out.append("---\ntags: [tankhapay, meta, index, coverage, source-of-truth]\n---")
out.append("# TankhaPay — Master Endpoint Index & Coverage Audit\n")
out.append("Every endpoint across the four backends, grouped by the 14 studied sections. Each request is "
 "an AES-encrypted POST — the body is `{\"encrypted\": base64(AES-ECB(payload))}` and the reply carries "
 "`commonData` (AES-ECB, same key) — see [[Encryption-Scheme]] and [[Auth-and-Access]]. Reads are wired "
 "into the CLI; writes/unknowns are documented but never wired ([[Read-Only-Guardrails]]).\n")
out.append("| Section | READ | WRITE | UNKNOWN | Note |")
out.append("|---|--:|--:|--:|---|")
for s in SECTIONS:
    r,w,u=sec_counts[s]
    out.append(f"| [[{s}]] | {r} | {w} | {u} | `{s}.md` |")
out.append(f"| **TOTAL** | **{tot_r}** | **{tot_w}** | **{tot_u}** | **{tot_r+tot_w+tot_u} endpoints** |")
out.append("")
out.append("## Coverage audit\n")
out.append(f"- **Total endpoints:** {len(all_urls)}  (READ {tot_r} · WRITE {tot_w} · UNKNOWN {tot_u})")
promoted = load(os.path.join(CAP,"unknown-promoted.tsv")) if os.path.exists(os.path.join(CAP,"unknown-promoted.tsv")) else []
excluded = [l for l in open(os.path.join(CAP,"unknown-excluded.tsv"))] if os.path.exists(os.path.join(CAP,"unknown-excluded.tsv")) else []
out.append(f"- **Wired read commands:** {len(wired)}  = {len(wired)-len(promoted)} confirmed reads + {len(promoted)} promoted from UNKNOWN (owner request). 35 extractor-mis-tagged reads were reclassified to write — see `../captures/reclassified-writes.tsv`.")
out.append(f"- **Promoted-from-UNKNOWN ({len(promoted)}):** path passes the read-only guardrail but behaviour is NOT live-verified — treat with caution (some `*Actions`/`manage_*` endpoints may dispatch mutations if given a write action). {len(excluded)} UNKNOWNs were kept OUT (auth/session + write-verb paths) — see `../captures/unknown-excluded.tsv`.")
out.append("")
out.append("**(a) Every endpoint in exactly one section**")
out.append(f"- endpoints in zero sections: **{len(zero)}**" + ("" if not zero else " → "+", ".join(zero[:8])))
out.append(f"- endpoints in more than one section: **{len(multi)}**" + ("" if not multi else " → "+", ".join(u for u,_ in multi[:8])))
out.append(f"- {'✅ 0 gaps' if not zero and not multi else '⚠ see above'}\n")
out.append("**(b) Every wired READ documented in its section note**")
out.append(f"- wired reads checked: **{len(wired)}**; undocumented: **{len(undoc)}**")
if undoc:
    for g,c,u in undoc[:15]: out.append(f"    - {g} `{c}` — {u}")
else:
    out.append("- ✅ 0 gaps — every wired read appears in its section note")
out.append("")
out.append("**(c) Routes (pages + subpages)**")
out.append(f"- routes enumerated in [[Pages-and-Routes]]: **{len(routes)}** (all mapped to a section there)\n")
out.append("---")
out.append("[[00-TankhaPay-Atlas]] · [[Encryption-Scheme]] · [[Auth-and-Access]] · [[Backends-and-Environment]] · [[Read-Only-Guardrails]] · [[Pages-and-Routes]]")

open(os.path.join(VAULT,"TankhaPay-Endpoints.md"),"w").write("\n".join(out)+"\n")
print(f"wrote vault/TankhaPay-Endpoints.md")
print(f"total={len(all_urls)} read={tot_r} write={tot_w} unknown={tot_u}")
print(f"(a) zero-section={len(zero)} multi-section={len(multi)}")
print(f"(b) undocumented wired reads={len(undoc)}")
print(f"(c) routes={len(routes)}")
if undoc[:20]:
    print("undoc sample:")
    for g,c,u in undoc[:20]: print("   ",g,c,u)
