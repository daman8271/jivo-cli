#!/usr/bin/env python3
"""Emit the operator-facing domain guide from the 20 domain studies.

The Printing Press regenerates README.md and the command help, but it knows
nothing about what a "returnable gatepass" is, that blowing data lives in Oil,
or that a gate-in {id} is the vehicle-entry id rather than the record's own.
That knowledge came out of the per-domain study and would otherwise be lost in
a workflow journal. This is the durable form of it.
"""
import json, re, os

D = ("/Users/damanpreetsingh/.claude/projects/-Users-damanpreetsingh-jivo-cli/"
     "e035ad0b-bcf0-443b-b65c-4a94696c4409/subagents/workflows/wf_82833d3b-265/journal.jsonl")

TITLE = {
    "attendance-security": "Attendance, security checks & weighbridge",
    "barcode": "Barcode traceability",
    "blowing": "Bottle blowing",
    "dashboards": "Dashboards & reporting",
    "dispatch": "Dispatch, dispatch plans & docking",
    "gate-core": "Gate core",
    "gatein-family": "Gate-in by material category",
    "grpo": "GRPO — goods receipt against PO",
    "labour": "Labour count & labour gate",
    "maintenance": "Maintenance",
    "marketplace-catalog": "Marketplace — catalogue & reconciliation",
    "marketplace-orders": "Marketplace — orders, dispatch & returns",
    "person-gatein": "Person gate-in — visitors, labour, contractors",
    "platform": "Platform — accounts, notifications, OMS bridge, AI",
    "production-execution": "Production execution",
    "production-planning": "Production planning, SAP bridge & POs",
    "quality-control": "Quality control",
    "returnable-items": "Returnable items",
    "vehicles": "Vehicles & drivers",
    "warehouse": "Warehouse — BST, BOM requests, FG receipts",
}

studies = {}
for line in open(D):
    try:
        d = json.loads(line)
    except Exception:
        continue
    if d.get("type") != "result":
        continue
    r = d.get("result")
    if isinstance(r, str):
        try:
            r = json.loads(r)
        except Exception:
            continue
    if isinstance(r, dict) and "endpoints" in r and "group" in r:
        studies[r["group"]] = r

def clean(t):
    t = (t or "").strip()
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t

out = []
w = out.append
w("---")
w('title: "Jivo Factory — domain guide"')
w("created: 2026-08-03")
w("updated: 2026-08-03")
w("project: jivogpt")
w("type: reference")
w("tags: [jivogpt, factory-cli, domains]")
w("---\n")
w("# Jivo Factory — what each domain actually means\n")
w("Written from a live study of the factory API on 2026-08-03: every domain was")
w("read out of the app's own frontend bundle and checked against live responses,")
w("then put through an adversarial review that tried to refute it.\n")
w("**Read the gotchas.** They are the difference between a command that returns")
w("a number and a command that returns the *right* number. Several were found")
w("only because a reviewer tried to prove the first answer wrong.\n")
w("Companion documents: [[CLI/factory-cli/MIGRATION-2026-08|what changed in v0.4.0]] ·")
w("[[CLI/factory-cli/research/SPEC-NOTES-2026-08|spec decisions & evidence]] ·")
w("[[CLI/factory-cli/research/API-FACTS|API facts]]\n")
w("## Contents\n")
for g in sorted(studies, key=lambda x: TITLE.get(x, x)):
    w(f"- [{TITLE.get(g, g)}](#{TITLE.get(g, g).lower().replace(' ', '-').replace('—','').replace('&','').replace(',','').replace('--','-')})")
w("")
for g in sorted(studies, key=lambda x: TITLE.get(x, x)):
    s = studies[g]
    w(f"\n---\n\n## {TITLE.get(g, g)}\n")
    w(f"*{len(s.get('endpoints') or [])} read commands · "
      f"{len(s.get('excluded_writes') or [])} write endpoints excluded*\n")
    w(clean(s.get("overview")) + "\n")
    got = clean(s.get("gotchas"))
    if got:
        w("### Traps\n")
        w(got + "\n")
    lost = s.get("lost_since_july") or []
    real = [x for x in lost if x and not x.lower().startswith(("nothing", "none"))]
    if real:
        w("### Gone or broken since July\n")
        for x in real:
            w(f"- {clean(x)}")
        w("")
    conf = clean(s.get("confidence"))
    if conf:
        w("### Confidence & open questions\n")
        w(conf + "\n")

path = "/Users/damanpreetsingh/jivo-cli/factory-cli/DOMAIN-GUIDE-2026-08.md"
open(path, "w").write("\n".join(out) + "\n")
print(f"wrote {path}")
print(f"  {len(studies)} domains, {sum(len(l) for l in out):,} chars")
