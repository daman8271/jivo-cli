#!/usr/bin/env python3
"""Merge every harvest source into one HARVEST.json for the domain-study phase.

Sources, in order of authority:
  1. probe-mart.jsonl / probe-oil-bev.jsonl  — LIVE evidence. A 200 is proof the
     endpoint exists; nothing a code-reading lens says can override it.
  2. the workflow's lens results (journal.jsonl, final `result` record)
  3. lens-client-wrappers.json / lens-query-hooks.json — the two lenses that
     died on context exhaustion inside the workflow and were relaunched
     standalone, writing to disk instead of returning inline.

Every endpoint carries how many independent lenses saw it (`lens_count`) and
what the live probe said (`live_status`), so the domain agents can weigh code
evidence against live evidence instead of trusting either blindly.
"""
import json
import os
import glob
import collections

SP = os.path.dirname(os.path.abspath(__file__))
WF = "/Users/damanpreetsingh/.claude/projects/-Users-damanpreetsingh-jivo-cli/e035ad0b-bcf0-443b-b65c-4a94696c4409/subagents/workflows/wf_1818c212-0f8/journal.jsonl"


def norm(p):
    if not p.startswith("/"):
        p = "/" + p
    return p.split("?")[0]


def domain_of(path):
    """Derive the domain from the path, never from the lens's own label.

    One lens names domains after the service-module constant (PERSON_GATEIN,
    MARKETPLACE, GATE_CORE) while the others use the URL segment
    (person-gatein, marketplace, gate-core). Trusting the label splits one
    domain across two buckets and would hand two agents half a domain each.
    The first path segment is unambiguous, so use it.
    """
    return path.strip("/").split("/")[0].lower().replace("_", "-")


def load_workflow_lenses():
    """Pull lens results out of the workflow journal.

    The journal carries two kinds of `result` record: one per lens, and — once
    the run finishes — a final aggregate that is already the reconciled union
    of those lenses (it carries a `counts` block). Counting both would inflate
    every endpoint's lens_count by one and destroy the corroboration signal we
    use to rank confidence. So: prefer the aggregate when it exists, and fall
    back to the raw per-lens results while the run is still in flight.
    """
    per_lens, aggregate = [], None
    if not os.path.exists(WF):
        return per_lens
    for line in open(WF):
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
        if not isinstance(r, dict):
            continue
        if "counts" in r and r.get("endpoints"):
            aggregate = r          # reconciled union — authoritative
        elif r.get("endpoints"):
            per_lens.append(r)

    if aggregate is not None:
        print("  using the workflow's reconciled aggregate "
              f"({len(aggregate['endpoints'])} endpoints, "
              f"{len(per_lens)} raw lens results superseded)")
        agg = dict(aggregate)
        agg["lens"] = "workflow-reconciled"
        return [agg]
    return per_lens


def load_standalone_lenses():
    out = []
    for fn in sorted(glob.glob(os.path.join(SP, "lens-*.json"))):
        try:
            out.append(json.load(open(fn)))
        except Exception as e:
            print(f"  ! could not parse {os.path.basename(fn)}: {e}")
    return out


def load_probe():
    """path -> {company: http}"""
    live = collections.defaultdict(dict)
    for fn in ("probe-mart.jsonl", "probe-oil-bev.jsonl"):
        p = os.path.join(SP, fn)
        if not os.path.exists(p):
            continue
        for line in open(p):
            r = json.loads(line)
            live[r["path"]][r["company"]] = r.get("http")
    return live


def main():
    lenses = load_workflow_lenses() + load_standalone_lenses()
    print(f"lens results loaded: {len(lenses)}")
    for l in lenses:
        print(f"  - {str(l.get('lens'))[:60]:60} {len(l.get('endpoints') or [])} endpoints")

    live = load_probe()
    merged = {}
    for l in lenses:
        lens_name = l.get("lens") or "?"
        for e in l.get("endpoints") or []:
            p = norm(e.get("path", ""))
            if not p:
                continue
            m = merged.setdefault(p, {
                "path": p,
                "methods": set(),
                "domain": domain_of(p),
                "semantic_name": "",
                "evidence": [],
                "query_params": set(),
                "lenses": set(),
                "is_mutation": False,
            })
            m["methods"] |= {x.upper() for x in (e.get("methods") or [])}
            m["query_params"] |= set(e.get("query_params") or [])
            m["lenses"].add(lens_name)
            # the reconciled aggregate already knows how many lenses saw this
            m["upstream_lens_count"] = max(m.get("upstream_lens_count", 0),
                                           int(e.get("lens_count") or 0))
            if e.get("is_mutation"):
                m["is_mutation"] = True
            if not m["semantic_name"] and e.get("semantic_name"):
                m["semantic_name"] = e["semantic_name"]
            ex = (e.get("evidence_excerpt") or "")[:200]
            if ex and len(m["evidence"]) < 3:
                m["evidence"].append({"file": e.get("evidence_file"), "excerpt": ex})

    # Fold in live-probe truth, including endpoints NO lens reported.
    for p, statuses in live.items():
        m = merged.get(p)
        if m is None and 200 in statuses.values():
            m = merged.setdefault(p, {
                "path": p, "methods": {"GET"},
                "domain": domain_of(p),
                "semantic_name": "", "evidence": [],
                "query_params": set(), "lenses": set(), "is_mutation": False,
            })
            m["lenses"].add("live-probe-only")
        if m is not None:
            m["live_status"] = {k.replace("JIVO_", ""): v for k, v in statuses.items()}

    out = []
    for p, m in sorted(merged.items()):
        ls = m.pop("lenses")
        rec = dict(m)
        rec["methods"] = sorted(m["methods"])
        rec["query_params"] = sorted(m["query_params"])
        rec["lens_count"] = max(len(ls), rec.pop("upstream_lens_count", 0))
        rec["lenses"] = sorted(ls)
        st = m.get("live_status") or {}
        rec["gettable_live"] = 200 in st.values()
        rec["write_only"] = (not rec["gettable_live"]) and 405 in st.values()
        rec["needs_params"] = 400 in st.values()
        out.append(rec)

    path = os.path.join(SP, "HARVEST.json")
    json.dump({"endpoints": out}, open(path, "w"), indent=1)

    gettable = [e for e in out if e["gettable_live"]]
    multi = [e for e in out if e["lens_count"] >= 2]
    doms = collections.Counter(e["domain"] for e in out)
    print(f"\nHARVEST.json written: {len(out)} distinct endpoints")
    print(f"  live GET (200 somewhere) : {len(gettable)}")
    print(f"  write-only (405, excluded): {sum(1 for e in out if e['write_only'])}")
    print(f"  need query params (400)   : {sum(1 for e in out if e['needs_params'])}")
    print(f"  corroborated by 2+ lenses : {len(multi)}")
    print(f"  single-lens only          : {sum(1 for e in out if e['lens_count'] == 1)}")
    print(f"\n  top domains: {doms.most_common(14)}")


if __name__ == "__main__":
    main()
