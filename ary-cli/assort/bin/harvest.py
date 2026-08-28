#!/usr/bin/env python3
"""Harvest workflow agent results into the ary assort research corpus.

The assortment research runs as multi-agent workflows. Each agent returns a
structured JSON object, and the workflow runtime records every one of them in its
journal.jsonl. This script reads those journals and files each result under
assort/research/<stage>/<key>.json, which is what `ary assort gaps`,
`ary assort priority` and `ary assort sweep` read.

Reading the journal — rather than the workflow's final return value — means a run
that dies half way still yields everything its agents had already produced.

Usage
    python3 assort/bin/harvest.py                      # all workflow runs found
    python3 assort/bin/harvest.py wf_96b430ed-466 …    # only these run ids
    python3 assort/bin/harvest.py --list               # what is on disk, no writes

Stage is inferred from the shape of each result, not from the agent's label, so a
renamed lane still lands in the right place.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
ASSORT = HERE.parent.parent                      # …/ary-cli/assort
CORPUS = ASSORT / "research"

# Every Claude Code session keeps its workflow transcripts under the project dir.
SESSIONS = Path.home() / ".claude" / "projects"

STAGES = ("demand", "coverage", "priority", "sweep", "verify")


def classify(res: dict) -> tuple[str, str] | None:
    """Return (stage, key) for a result object, or None if it is not one of ours."""
    if not isinstance(res, dict):
        return None

    # demand: the ideal assortment, built blind to ARY
    if "skuLines" in res and res.get("category"):
        return "demand", res["category"]

    # coverage: that list diffed against ARY's live catalogue
    if "lines" in res and res.get("category"):
        return "coverage", res["category"]

    # priority: the ranked, rupee-sized recommendation
    if "recommendations" in res and res.get("category"):
        return "priority", res["category"]

    # verify / stress: an adversarial pass over a lane
    if "verdicts" in res and res.get("lane"):
        return "verify", res["lane"]

    # sweep / reality: an investigation lane
    if "findings" in res and res.get("lane"):
        return "sweep", res["lane"]

    # the stress lanes wrap {plan, stress} — unwrap and file both halves
    if "plan" in res and "stress" in res:
        return "wrapped", ""

    # the intelligence sweep wraps {finding, verify}
    if "finding" in res and "verify" in res:
        return "wrapped", ""

    return None


def unwrap(res: dict) -> list[dict]:
    """Flatten the {plan,stress} / {finding,verify} wrappers into their parts."""
    out = []
    for k in ("plan", "finding", "stress", "verify"):
        v = res.get(k)
        if isinstance(v, dict):
            out.append(v)
    return out


def safe(name: str) -> str:
    """Filesystem-safe corpus key."""
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", str(name)).strip("-")
    return s or "unnamed"


def journals(run_ids: list[str]) -> list[Path]:
    found = []
    if not SESSIONS.is_dir():
        return found
    for j in SESSIONS.glob("*/*/subagents/workflows/*/journal.jsonl"):
        run = j.parent.name
        if run_ids and not any(r in run for r in run_ids):
            continue
        found.append(j)
    return sorted(found)


def main(argv: list[str]) -> int:
    list_only = "--list" in argv
    run_ids = [a for a in argv if not a.startswith("-")]

    js = journals(run_ids)
    if not js:
        print("no workflow journals found"
              + (f" for {run_ids}" if run_ids else ""), file=sys.stderr)
        return 1

    results: dict[tuple[str, str], dict] = {}
    seen = skipped = 0

    for j in js:
        for line in j.read_text(errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("type") != "result":
                continue
            res = rec.get("result")
            seen += 1

            queue = [res]
            while queue:
                item = queue.pop()
                c = classify(item)
                if c is None:
                    skipped += 1
                    continue
                stage, key = c
                if stage == "wrapped":
                    queue.extend(unwrap(item))
                    continue
                # later results for the same key win: a resumed run supersedes
                results[(stage, safe(key))] = item

    if list_only:
        by_stage: dict[str, list[str]] = {s: [] for s in STAGES}
        for (stage, key) in sorted(results):
            by_stage.setdefault(stage, []).append(key)
        for stage in STAGES:
            keys = by_stage.get(stage, [])
            print(f"{stage:9} {len(keys):3}  {' '.join(sorted(keys))}")
        print(f"\n{seen} result records read from {len(js)} journal(s); "
              f"{skipped} not classifiable")
        return 0

    written = 0
    for (stage, key), obj in sorted(results.items()):
        d = CORPUS / stage
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{key}.json").write_text(json.dumps(obj, indent=2, ensure_ascii=False))
        written += 1

    print(f"harvested {written} result(s) into {CORPUS}")
    for stage in STAGES:
        n = len([1 for (s, _) in results if s == stage])
        if n:
            print(f"  {stage:9} {n}")
    if skipped:
        print(f"  ({skipped} result records did not match a known corpus shape)")
    print(f"\nnow run:  ary assort research")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
