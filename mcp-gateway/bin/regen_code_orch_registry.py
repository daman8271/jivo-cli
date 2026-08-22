#!/usr/bin/env python3
"""Fill codeOrchEndpoints from tools-manifest.json for endpoints the sweep added
to the CLI but never regenerated into the MCP registry."""
import json, re, sys, pathlib

mod = pathlib.Path(sys.argv[1])
go  = mod / "internal/mcp/code_orch.go"
man = mod / "tools-manifest.json"

src = go.read_text()
tools = json.load(open(man))["tools"]

have = set(re.findall(r'ID:\s*"([A-Za-z0-9._-]+)"', src))

def to_id(name):           # dc_get-details -> dc.get-details
    return name.replace("_", ".", 1)

def gostr(s):
    return json.dumps(s if s is not None else "", ensure_ascii=False)

added, skipped_nonget = [], []
for t in tools:
    tid = to_id(t["name"])
    if tid in have:
        continue
    if (t.get("method") or "GET").upper() != "GET":
        skipped_nonget.append((tid, t.get("method")))
        continue
    path = t.get("path", "")
    summary = " ".join((t.get("description") or "").split())
    placeholders = re.findall(r"\{([A-Za-z0-9_]+)\}", path)
    group, _, rest = t["name"].partition("_")
    pos = "".join(f"{gostr(p)}, " for p in placeholders)
    added.append(
        "\t{\n"
        f"\t\tID:             {gostr(tid)},\n"
        f"\t\tMethod:         \"GET\",\n"
        f"\t\tPath:           {gostr(path)},\n"
        f"\t\tSummary:        {gostr(summary)},\n"
        f"\t\tPositional:     []string{{{pos.rstrip(', ')}}},\n"
        "\t\tTemplateParams: []codeOrchParamBinding{},\n"
        "\t\tQueryParams:    []codeOrchParamBinding{},\n"
        f"\t\tkeywords:       codeOrchKeywords({gostr(group)}, {gostr(rest)}, {gostr(summary)}, {gostr(path)}),\n"
        "\t},\n"
    )

if not added:
    print(f"  {mod.name}: nothing to add (registry already complete)")
    sys.exit(0)

anchor = "var codeOrchEndpoints = []codeOrchEndpoint{\n"
if anchor not in src:
    print(f"  {mod.name}: ANCHOR NOT FOUND — aborting", file=sys.stderr); sys.exit(1)

src = src.replace(anchor, anchor + "".join(added), 1)
go.write_text(src)
print(f"  {mod.name}: added {len(added)} endpoints" + (f", skipped {len(skipped_nonget)} non-GET {skipped_nonget}" if skipped_nonget else ""))
