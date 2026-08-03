#!/usr/bin/env python3
"""Surface verifier findings the automated merge cannot apply.

The workflow's post-processing can REMOVE an endpoint a verifier refuted, but it
cannot ADD one. That matters because a refutation is ambiguous — it can mean
either "you wrongly published this" or "you wrongly EXCLUDED this". The second
kind is a recovered read, and it is silently lost.

Real example: /returnable-items/returnable-attachments/{id}/ was excluded as
DELETE-only because the React app only ever calls delete on it. A live GET with
a real attachment id returns the object, so it should ship. Harvested methods
describe what the CLIENT calls, not what the SERVER allows.

This script separates the two kinds and prints everything a human must decide.

usage: extract_recoveries.py
"""
import json
import re

WF = ("/Users/damanpreetsingh/.claude/projects/-Users-damanpreetsingh-jivo-cli/"
      "e035ad0b-bcf0-443b-b65c-4a94696c4409/subagents/workflows/wf_82833d3b-265/journal.jsonl")

RECOVERY_HINT = re.compile(
    r"wrongly excluded|should be published|publish the get|refuted as a write-only|"
    r"belongs in endpoints|not a write|is readable|live get .*(returns|works)",
    re.I)


def load():
    studies, verdicts = {}, []
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
        if "refuted" in r:
            verdicts.append(r)
        elif "endpoints" in r and "group" in r:
            studies[r["group"]] = r
    return studies, verdicts


def main():
    studies, verdicts = load()
    print(f"studies={len(studies)}  verdicts={len(verdicts)}\n")

    recoveries, removals, unclear = [], [], []
    for v in verdicts:
        g = v.get("group")
        published = {e["path"] for e in (studies.get(g, {}).get("endpoints") or [])}
        for x in (v.get("refuted") or []):
            p, reason = x.get("path", ""), x.get("reason", "") or ""
            if p in published:
                removals.append((g, p, reason))
            elif RECOVERY_HINT.search(reason):
                recoveries.append((g, p, reason))
            else:
                unclear.append((g, p, reason))

    print("=" * 78)
    print(f"RECOVERED READS — refuted EXCLUSIONS, i.e. publish these ({len(recoveries)})")
    print("=" * 78)
    for g, p, r in recoveries:
        print(f"\n[{g}] {p}\n    {r[:400]}")

    print("\n" + "=" * 78)
    print(f"REMOVALS — refuted PUBLISHED endpoints, already dropped by the merge ({len(removals)})")
    print("=" * 78)
    for g, p, r in removals:
        print(f"  [{g}] {p} — {r[:150]}")

    if unclear:
        print("\n" + "=" * 78)
        print(f"AMBIGUOUS — refuted a path that is neither published nor obviously a recovery ({len(unclear)})")
        print("  (read these by hand; the merge did nothing with them)")
        print("=" * 78)
        for g, p, r in unclear:
            print(f"\n[{g}] {p}\n    {r[:300]}")

    # Safety findings must never be lost in the noise.
    leaks = [(v.get("group"), x) for v in verdicts for x in (v.get("write_leaks") or [])]
    sidefx = [(v.get("group"), x) for v in verdicts for x in (v.get("unflagged_side_effects") or [])]
    print("\n" + "=" * 78)
    print(f"SAFETY — write leaks ({len(leaks)}) and unflagged side effects ({len(sidefx)})")
    print("=" * 78)
    for g, x in leaks:
        print(f"  WRITE LEAK  [{g}] {x}")
    for g, x in sidefx:
        print(f"  SIDE EFFECT [{g}] {x}")
    if not leaks and not sidefx:
        print("  none reported")


if __name__ == "__main__":
    main()
