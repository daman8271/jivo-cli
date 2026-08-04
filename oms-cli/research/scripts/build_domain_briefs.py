#!/usr/bin/env python3
"""Build one self-contained briefing file per domain for the phase-3 studies.

Each brief carries, per endpoint: the SHIPPED command name (if any), the live
probe outcome, the server's own error text, the observed params, the harvest
evidence and the write-verb flags. The point is that a study agent never has to
re-derive any of it — and, more importantly, can never invent a command name for
an endpoint that already has one.

Skill rule 6: existing endpoints keep their existing command names. Domain
agents invent fresh names without knowing the shipped ones; on factory that
renamed 102 working commands and would have broken every script and MCP
endpoint_id referencing them. The shipped name is therefore printed as a
non-negotiable field, not offered as a suggestion.

usage: build_domain_briefs.py <inventory.json> <spec.yaml> <probe-bare.jsonl>
                              <probe-branch.jsonl> <outdir>
"""
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from normalise import norm  # noqa: E402

# Which study owns which path prefix. Grouped by what an operator would call
# one subject area, not by URL tidiness.
GROUPS = {
    "hana":       ["/api/hana/"],
    "orders":     ["/api/orders/"],
    "sap":        ["/api/sap/", "/api/service-layer/"],
    "tracker":    ["/api/tracker/"],
    "account":    ["/api/auth/", "/api/admin/", "/api/devices/", "/api/ui-config/"],
    "invoices":   ["/api/invoice/", "/api/sku/", "/api/legal/"],
}


def shipped_index(spec_path):
    """normalised path -> 'resource endpoint' plus the declared param block."""
    txt = open(spec_path).read()
    out, res, ep, buf = {}, None, None, []
    lines = txt.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"^  ([\w-]+):\s*$", line)
        if m:
            res = m.group(1)
            continue
        m = re.match(r"^      ([\w-]+):\s*$", line)
        if m:
            ep = m.group(1)
            continue
        m = re.match(r'^\s+path: "([^"]+)"', line)
        if m and res and ep and m.group(1).startswith("/api"):
            block = []
            for j in range(i, min(len(lines), i + 40)):
                if j > i and re.match(r"^      [\w-]+:\s*$", lines[j]):
                    break
                block.append(lines[j])
            out[norm(m.group(1))] = {
                "command": f"{res} {ep}",
                "resource": res,
                "spec_block": "\n".join(block).rstrip(),
            }
    return out


def main():
    inv = json.load(open(sys.argv[1]))["inventory"]
    shipped = shipped_index(sys.argv[2])
    probes = defaultdict(list)
    for f in (sys.argv[3], sys.argv[4]):
        for line in open(f):
            r = json.loads(line)
            probes[norm(r["path"])].append(r)
    outdir = sys.argv[5]
    os.makedirs(outdir, exist_ok=True)

    groups = defaultdict(list)
    for e in inv:
        for g, prefixes in GROUPS.items():
            if any(e["path"].startswith(p.rstrip("/")) for p in prefixes):
                groups[g].append(e)
                break
        else:
            groups["_ungrouped"].append(e)

    # A shipped endpoint that the harvest missed must still reach a study.
    for p, meta in shipped.items():
        if any(p == e["path"] for e in inv):
            continue
        for g, prefixes in GROUPS.items():
            if any(p.startswith(x.rstrip("/")) for x in prefixes):
                groups[g].append({"path": p, "domain": p.split("/")[2],
                                  "methods": ["GET"], "lenses": ["shipped-only"],
                                  "params": [], "notes": ["NOT called by the current SPA"],
                                  "in_shipped_spec": meta["command"], "get_capable": True,
                                  "raw": [p]})
                break

    for g, entries in sorted(groups.items()):
        lines = [f"# Domain brief: {g}", ""]
        lines += [f"{len(entries)} paths. Live probe evidence and shipped command names "
                  f"are given per endpoint. Do not invent a command name for an endpoint "
                  f"that already has one.", ""]
        for e in sorted(entries, key=lambda x: x["path"]):
            p = e["path"]
            sh = shipped.get(p)
            lines.append(f"## `{p}`")
            lines.append("")
            lines.append(f"- harvested methods: `{', '.join(e['methods'])}`"
                         f"  | GET-capable: **{e['get_capable']}**")
            lines.append(f"- lenses: {', '.join(e['lenses'])}")
            if e["params"]:
                lines.append(f"- params observed at the call site: `{', '.join(e['params'])}`")
            if e["notes"]:
                lines.append(f"- flags: {', '.join(e['notes'])}")
            if sh:
                lines.append(f"- **SHIPPED COMMAND (must not be renamed): "
                             f"`oms-pp-cli {sh['command']}`**")
                lines.append("")
                lines.append("  shipped spec block:")
                lines.append("  ```yaml")
                lines += ["  " + x for x in sh["spec_block"].split("\n")]
                lines.append("  ```")
            else:
                lines.append("- NEW — not in the shipped spec; needs a command name")
            recs = probes.get(p, [])
            if recs:
                lines.append("")
                lines.append("  live probe:")
                for r in sorted(recs, key=lambda x: x.get("branch", "")):
                    b = f"branch={r['branch']}" if r.get("branch") else "bare (no params)"
                    line = f"  - {b} -> **HTTP {r['http']}**"
                    if r.get("rows") is not None:
                        line += f", rows={r['rows']}"
                    if r.get("bytes"):
                        line += f", {r['bytes']} bytes"
                    if r.get("json_top"):
                        line += f", top-level JSON `{r['json_top']}`"
                    lines.append(line)
                    if r.get("error"):
                        lines.append(f"    - server said: `{r['error'][:300].strip()}`")
                    elif r.get("sample_text"):
                        lines.append(f"    - sample: `{r['sample_text'][:300]}`")
            else:
                lines.append("")
                lines.append("  live probe: **not probed** "
                             "(parameterised path, or write-intent — see WRITE_INTENT in probe.py)")
            lines.append("")
        open(os.path.join(outdir, f"brief-{g}.md"), "w").write("\n".join(lines))
        print(f"  brief-{g}.md  ({len(entries)} paths)")


if __name__ == "__main__":
    main()
