#!/usr/bin/env python3
"""Reconcile the registry lens against the shipped 138-endpoint spec, and
decide what may be probed.

Two rules drive the probe set:

 * RULE 0 / skill rule 1 - a path whose ONLY observed verb is a write, and
   which the shipped spec never published, is never probed and never
   published. Probing it buys nothing (it could not be published either way)
   and a bare GET to an action route is exactly the get_or_create shape that
   created six production rows on factory.

 * skill rule 5 / spec-and-reprint - a path the shipped spec already
   publishes as GET is proven GET-serving by the fact that it shipped. It
   gets probed regardless of what verb the current client happens to use,
   because dropping it needs positive justification.
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalise import norm  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# Path segments that mark an action route. Matched on the LAST segment of the
# normalised path so a resource literally named e.g. "updates" is not caught.
ACTION_TAILS = {
    "add", "update", "delete", "create", "remove", "bulk-upsert", "upsert",
    "preview", "refresh", "set-target", "mark-read", "mark-all-read",
    "manual-import", "manual-plan", "approve", "reject", "submit", "dispatch",
    "verify", "change-password", "login", "logout", "message", "import",
    "reorder", "assign", "unassign", "cancel", "confirm", "commit",
}


def is_action(path):
    tail = [s for s in path.split("/") if s and s != "{}"]
    return bool(tail) and tail[-1] in ACTION_TAILS


def main():
    reg = [json.loads(l) for l in open(os.path.join(HERE, "lens1-registry.jsonl"))]
    old_rows = [l.rstrip("\n").split("\t") for l in
                open(os.path.join(HERE, "OLD-SPEC.tsv")) if l.strip()]
    old = {norm(p): (res, ep) for res, ep, p in old_rows}

    by_path = collections.defaultdict(lambda: {"methods": set(), "fns": set(),
                                               "svc": set(), "params": set(),
                                               "raw": set(), "chunk": set()})
    for r in reg:
        d = by_path[r["path"]]
        d["methods"].add(r["method"])
        if r["fn_name"]:
            d["fns"].add(r["fn_name"])
        if r["service_var"]:
            d["svc"].add(r["service_var"])
        d["params"].update(r["query_params"])
        d["raw"].add(r["raw_path"])
        d["chunk"].add(r["chunk"])

    out = {}
    for p, d in by_path.items():
        get_capable = "GET" in d["methods"]
        in_old = p in old
        write_only = not get_capable
        parameterised = "{}" in p
        action = is_action(p)
        if in_old:
            decision, why = "PROBE", "shipped in v0.1.0 spec"
        elif write_only and (action or True):
            decision, why = "EXCLUDE_WRITE", f"client only ever {'/'.join(sorted(d['methods']))}s it; new since v0.1.0"
        elif action:
            decision, why = "EXCLUDE_ACTION", "action-shaped route; not probed (rule 1)"
        else:
            decision, why = "PROBE", "GET-capable in client"
        if decision == "PROBE" and parameterised:
            decision, why = "PROBE_SKIP_PARAM", why + "; parameterised, cannot probe without a real id"
        out[p] = {
            "path": p, "methods": sorted(d["methods"]), "get_capable": get_capable,
            "in_old_spec": in_old,
            "old_command": "%s %s" % old[p] if in_old else None,
            "fn_names": sorted(d["fns"]), "service_vars": sorted(d["svc"]),
            "client_query_params": sorted(d["params"]),
            "raw_paths": sorted(x for x in d["raw"] if x),
            "chunks": sorted(d["chunk"]),
            "parameterised": parameterised, "action_shaped": action,
            "decision": decision, "why": why,
            "domain": ([s for s in p.split("/") if s] + ["?"])[1],
        }

    # Endpoints the shipped spec has that the current client no longer calls.
    for p, (res, ep) in old.items():
        if p not in out:
            out[p] = {
                "path": p, "methods": [], "get_capable": None, "in_old_spec": True,
                "old_command": f"{res} {ep}", "fn_names": [], "service_vars": [],
                "client_query_params": [], "raw_paths": [], "chunks": [],
                "parameterised": "{}" in p, "action_shaped": is_action(p),
                "decision": "PROBE_SKIP_PARAM" if "{}" in p else "PROBE",
                "why": "shipped in v0.1.0 but the current client no longer calls it - "
                       "probe before assuming dead",
                "domain": ([s for s in p.split("/") if s] + ["?"])[1],
            }

    with open(os.path.join(HERE, "reconciled.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)

    c = collections.Counter(v["decision"] for v in out.values())
    print("total distinct normalised paths:", len(out))
    for k, v in sorted(c.items()):
        print(f"  {k:20} {v}")
    probe = sorted(p for p, v in out.items() if v["decision"] == "PROBE")
    open(os.path.join(HERE, "probe-paths.txt"), "w").write("\n".join(probe) + "\n")
    print(f"\nprobe set (non-parameterised): {len(probe)} -> probe-paths.txt")

    print("\n== new since v0.1.0, GET-capable, probeable ==")
    for p in probe:
        if not out[p]["in_old_spec"]:
            print("  +", p, out[p]["fn_names"])
    print("\n== shipped in v0.1.0 but client no longer calls ==")
    for p, v in sorted(out.items()):
        if v["in_old_spec"] and not v["methods"]:
            print("  ?", p, "->", v["old_command"])
    print("\n== excluded writes (new, never GET in client) ==")
    for p, v in sorted(out.items()):
        if v["decision"] == "EXCLUDE_WRITE":
            print("  x", p, v["methods"], v["fn_names"])


if __name__ == "__main__":
    main()
