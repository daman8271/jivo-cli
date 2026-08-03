#!/usr/bin/env python3
"""Apply the adversarial verdicts to the domain studies, producing DOMAINS.json.

The workflow's own post-processing did this in-script, but its final return
value never reached the journal — so it is redone here, which is better anyway:
the logic is now inspectable, and the two verdicts that had to be re-run
standalone (warehouse, production-execution) drop straight in from disk.

A refutation is AMBIGUOUS by nature. It can mean:
  * "you wrongly published this"  -> remove the endpoint
  * "you wrongly EXCLUDED this"   -> a recovered read, must be added back
Only the first is safe to automate. The second is reported for a human, because
adding an endpoint to a read-only surface is exactly the decision that must not
be made by a regex.
"""
import json
import os
import re
import collections

SP = os.path.dirname(os.path.abspath(__file__))
WF = ("/Users/damanpreetsingh/.claude/projects/-Users-damanpreetsingh-jivo-cli/"
      "e035ad0b-bcf0-443b-b65c-4a94696c4409/subagents/workflows/wf_82833d3b-265/journal.jsonl")

RECOVERY_HINT = re.compile(
    r"wrongly excluded|should be published|publish the get|refuted as a write-only|"
    r"belongs in endpoints|is readable", re.I)

# A "refutation" almost never means "delete this endpoint". In practice the
# verifiers used the field for any claim they disproved — a wrong `companies`
# list, a wrong response_shape detail, a gotcha that did not reproduce. Treating
# all of those as deletions removed 28 endpoints that v0.3.0 ships and that
# still return live 200s: /grpo/pending/, /maintenance/assets/,
# /quality-control/production-qc/, /notifications/unread-count/ and more.
#
# So: only delete when the reason says the ENDPOINT itself must not ship.
# Everything else is a correction to the metadata, and the endpoint stays.
DELETE_REASON = re.compile(
    r"hallucinat|does not exist|doesn't exist|no such (?:endpoint|path|route)|"
    r"not routed|returns 404|is a 404|404s|"
    r"write[- ]only|is a write|must not be published|never be published|"
    r"mutates on get|get_or_create|creates a row|creates production",
    re.I)


_LIVE = None


def live_200(path):
    """True when a bare GET on this path returned 200 in the 2026-08-03 probe.

    This is the ground truth the whole pipeline rests on. Code evidence (what
    the bundle calls) and prose evidence (what a reviewer wrote) are both weaker
    than an observed 200, and must never be allowed to delete an endpoint that
    demonstrably serves reads.
    """
    global _LIVE
    if _LIVE is None:
        _LIVE = {}
        for fn in ("probe-mart.jsonl", "probe-oil-bev.jsonl"):
            p = os.path.join(SP, fn)
            if not os.path.exists(p):
                continue
            for line in open(p):
                r = json.loads(line)
                if r.get("http") == 200:
                    _LIVE[r["path"]] = True
    return _LIVE.get(path, False)


def load():
    studies, verdicts = {}, {}
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
        if "refuted" in r and r.get("group"):
            verdicts[r["group"]] = r
        elif "endpoints" in r and r.get("group"):
            studies[r["group"]] = r
    # verdicts re-run standalone after the workflow's transport failures
    for fn in sorted(os.listdir(SP)):
        if fn.startswith("verdict-") and fn.endswith(".json"):
            try:
                v = json.load(open(os.path.join(SP, fn)))
            except Exception as e:
                print(f"  ! {fn} unreadable: {e}")
                continue
            if v.get("group"):
                verdicts[v["group"]] = v
                print(f"  + standalone verdict: {v['group']}")
    return studies, verdicts


def main():
    studies, verdicts = load()
    print(f"studies={len(studies)}  verdicts={len(verdicts)}")
    missing = sorted(set(studies) - set(verdicts))
    if missing:
        print(f"  UNVERIFIED (shipping without adversarial review): {missing}")

    domains, recoveries, removed_total = [], [], 0
    # Every path any verdict removed, persisted so DOWNSTREAM steps cannot
    # resurrect it. The carry-forward rule in assemble_spec.py re-publishes
    # v0.3.0 endpoints that no study proposed — without this list it happily
    # restored three endpoints the verifiers had flagged as unsafe.
    killed_all = set()
    for g, s in studies.items():
        v = verdicts.get(g)
        kill, claim_fixes = set(), collections.defaultdict(list)
        if v:
            published = {e["path"] for e in s.get("endpoints", [])}
            for x in (v.get("refuted") or []):
                p, reason = x.get("path", ""), (x.get("reason") or "")
                if p in published:
                    # Ground truth first. A bare GET that returned 200 proves the
                    # endpoint exists and is readable; no sentence can override
                    # that. Keyword-matching prose for deletion decisions is
                    # unreliable — "a parameter name that does not exist on this
                    # serializer" matched a rule meant for "this endpoint does
                    # not exist", and deleted a live, working command.
                    if live_200(p):
                        claim_fixes[p].append(reason[:400])
                    elif DELETE_REASON.search(reason):
                        kill.add(p)                 # unprobed AND said to be bogus
                    else:
                        claim_fixes[p].append(reason[:400])   # a CLAIM was wrong
                elif RECOVERY_HINT.search(reason):
                    recoveries.append((g, p, reason[:300]))
            # These two ARE endpoint-level safety judgements, so they still delete.
            kill |= set(v.get("write_leaks") or [])
            kill |= set(v.get("unflagged_side_effects") or [])

        # fail closed on anything the author itself flagged
        for e in s.get("endpoints", []):
            if (e.get("side_effect_risk") or "none") != "none":
                kill.add(e["path"])

        corrections = collections.defaultdict(list)
        for c in ((v or {}).get("corrected") or []):
            corrections[c.get("path")].append(
                f"{c.get('field')}: {c.get('should_be')}")

        killed_all |= kill
        kept = []
        for e in s.get("endpoints", []):
            if e["path"] in kill:
                removed_total += 1
                continue
            fixes = list(corrections.get(e["path"], [])) + list(claim_fixes.get(e["path"], []))
            if fixes:
                e = {**e, "corrections": fixes}
            kept.append(e)

        domains.append({**s, "endpoints": kept,
                        "verified_adversarially": bool(v),
                        "verifier_verdict": (v or {}).get("verdict", "")})

    json.dump({"domains": domains}, open(os.path.join(SP, "DOMAINS.json"), "w"), indent=1)
    json.dump(sorted(killed_all), open(os.path.join(SP, "VERDICT-KILLS.json"), "w"), indent=1)
    print(f"  VERDICT-KILLS.json: {len(killed_all)} paths no downstream step may republish")
    total = sum(len(d["endpoints"]) for d in domains)
    fixed = sum(1 for d in domains for e in d["endpoints"] if e.get("corrections"))
    print(f"\nDOMAINS.json written: {len(domains)} domains, {total} endpoints")
    print(f"  removed by verdicts (endpoint must not ship): {removed_total}")
    print(f"  kept with corrected metadata (a claim was wrong): {fixed}")
    if recoveries:
        print(f"\nRECOVERED READS needing a human decision ({len(recoveries)}):")
        for g, p, why in recoveries:
            print(f"  [{g}] {p}\n      {why[:200]}")


if __name__ == "__main__":
    main()
