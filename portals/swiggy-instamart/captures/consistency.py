#!/usr/bin/env python3
"""
consistency.py — PHASE-9 sweep tool: does every number the prose claims still
match the artifacts on disk?

Written because sweep 2 found stale counts in three hand-written notes after the
extractor gained endpoints and the walk gained a pass. Prose drifts; generated
files do not. This makes the drift mechanical to find instead of a memory test.

Reports GROUND TRUTH, then every stale claim it can find. Exit 1 if any drift.
"""
import csv
import glob
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VAULT = os.path.join(ROOT, "vault")


def truth():
    rows = list(csv.DictReader(open(os.path.join(HERE, "endpoints-raw.tsv")), delimiter="\t"))
    cls = Counter(r["class"] for r in rows)
    routes = sum(1 for i, _ in enumerate(open(os.path.join(HERE, "routes-raw.txt"))) if i)
    shots = glob.glob(os.path.join(HERE, "walk*", "*.png"))
    notes = glob.glob(os.path.join(VAULT, "**", "*.md"), recursive=True)
    corpus = glob.glob(os.path.join(HERE, "js", "*", "*.js"))
    passes = sorted({os.path.basename(os.path.dirname(p)) for p in shots})
    nonget = list(csv.DictReader(open(os.path.join(HERE, "nonget-allowed.tsv")), delimiter="\t")) \
        if os.path.exists(os.path.join(HERE, "nonget-allowed.tsv")) else []
    flagged = list(csv.DictReader(open(os.path.join(HERE, "nonget-flagged.tsv")), delimiter="\t")) \
        if os.path.exists(os.path.join(HERE, "nonget-flagged.tsv")) else []
    return {
        "endpoints": len(rows),
        "read": cls["READ"] + cls["READ_FILE"],
        "write": cls["WRITE"],
        "export": cls["EXPORT"],
        "unknown": cls["UNKNOWN"],
        "wired": sum(1 for r in rows if r["wired"] == "yes"),
        "routes": routes,
        "screenshots": len(shots),
        "walk_passes": len(passes),
        "notes": len(notes),
        "corpus_files": len(corpus),
        "corpus_mb": round(sum(os.path.getsize(p) for p in corpus) / 1024 / 1024, 1),
        "nonget_allowed": len(nonget),
        "nonget_flagged": len(flagged),
    }


# (claim regex, truth key, human label). The regex must capture the number in \1.
CLAIMS = [
    (r"\*\*(\d+) distinct endpoints\*\*", "endpoints", "distinct endpoints"),
    (r"\*\*(\d+)\*\* distinct endpoint contracts", "endpoints", "endpoint contracts"),
    (r"all (\d+) catalogued endpoints", "endpoints", "catalogued endpoints"),
    (r"Of \*\*(\d+)\*\* catalogued endpoints", "endpoints", "catalogued endpoints"),
    (r"\*\*(\d+) distinct \(host, path\) endpoint contracts\*\*", "endpoints", "endpoint contracts"),
    (r"\*\*(\d+)\*\* endpoints whose HTTP method could not be proven", "unknown", "UNKNOWN endpoints"),
    (r"\*\*(\d+) UNKNOWN endpoints\*\* remain", "unknown", "UNKNOWN endpoints"),
    (r"(\d+) `UNKNOWN`\n", "unknown", "UNKNOWN rows"),
    # deliberately anchored on "distinct routes"/"SPA routes across": a bare
    # "**12 SPA routes**" in Study-Verification is a DELTA (routes lost to a
    # regression and recovered), not a total, and matching it was a false positive.
    (r"\*\*(\d+) route literals\*\*", "routes", "route literals"),
    (r"\*\*(\d+) SPA routes\*\*; \*\*6 remotes", "routes", "SPA routes"),
    (r"\*\*(\d+)\*\* screenshots", "screenshots", "screenshots"),
    (r"\*\*(\d+) screenshots across", "screenshots", "screenshots"),
    (r"— (\d+) wikilinked Obsidian notes", "notes", "vault notes"),
    (r"\*\*(\d+) / \d+ vault notes present\*\*", "notes", "vault notes"),
    (r"\((\d+) files / [\d.]+ MB", "corpus_files", "corpus files"),
    (r"\*\*(\d+) rows\*\*, every app-fired non-GET", "nonget_allowed", "non-GET rows"),
    # Atlas "Study status" phrasing — this block went stale twice and the earlier
    # patterns did not cover it, so it is matched explicitly.
    (r"section notes · (\d+) distinct endpoint contracts", "endpoints", "endpoint contracts (Atlas)"),
    (r"contracts · (\d+) route literals", "routes", "route literals (Atlas)"),
    (r"route literals · (\d+) screenshots", "screenshots", "screenshots (Atlas)"),
    (r"screenshots ·\n(\d+) live walk passes", "walk_passes", "walk passes (Atlas)"),
    (r"\*\*(\d+) read-safe\*\*", "read", "read-safe"),
    (r"\*\*(\d+) UNKNOWN\*\* \(documented", "unknown", "UNKNOWN (Atlas)"),
    (r"\*\*(\d+)\*\* reads have a proven method", "wired", "wired reads"),
    (r"\*\*(\d+) read commands", "wired", "read commands (cli README)"),
    (r"\*\*(\d+)\*\* rows classified `READ`", "read", "READ rows"),
    (r"the \*\*(\d+)\*\* paths classified", "wired", "allowlisted paths"),
    (r"only the (\d+) paths the study classified", "wired", "allowlisted paths"),
]

# per-host endpoint counts must match too
def host_truth():
    import csv as _csv
    from collections import Counter as _C
    return _C(r["host"] for r in _csv.DictReader(
        open(os.path.join(HERE, "endpoints-raw.tsv")), delimiter="\t"))


def main():
    T = truth()
    print("GROUND TRUTH (from the artifacts on disk)")
    for k, v in T.items():
        print(f"  {k:18s} {v}")
    print()

    drift = []
    for p in sorted(glob.glob(os.path.join(VAULT, "**", "*.md"), recursive=True)
                    + [os.path.join(ROOT, "README.md"),
                       os.path.join(ROOT, "cli", "README.md"),
                       os.path.join(ROOT, "COVERAGE-LEDGER.md")]):
        if not os.path.exists(p):
            continue
        txt = open(p, encoding="utf-8", errors="replace").read()
        for rx, key, label in CLAIMS:
            for m in re.finditer(rx, txt):
                got = int(m.group(1))
                if got != T[key]:
                    drift.append((os.path.relpath(p, ROOT), label, got, T[key],
                                  txt[max(0, m.start() - 40):m.end() + 20].replace("\n", " ")))
    # per-host table rows: | `host` | ... | N |
    HT = host_truth()
    for p in [os.path.join(VAULT, "00-Swiggy-Instamart-Atlas.md"),
              os.path.join(VAULT, "Swiggy-Instamart-Endpoints.md")]:
        if not os.path.exists(p):
            continue
        for m in re.finditer(r"\|\s*\*?\*?`([a-z0-9.\-]+\.swiggy\.com)`\*?\*?\s*\|[^|]*\|\s*(\d+)\s*\|",
                             open(p, encoding="utf-8").read()):
            host, got = m.group(1), int(m.group(2))
            if host in HT and got != HT[host]:
                drift.append((os.path.relpath(p, ROOT), f"endpoints on {host}", got, HT[host], m.group(0)[:90]))

    if drift:
        print(f"STALE CLAIMS: {len(drift)}")
        for f, label, got, want, ctx in drift:
            print(f"  {f}: says {got} {label}, truth is {want}")
            print(f"      …{ctx}…")
    else:
        print("STALE CLAIMS: none — every checked number matches the artifacts.")
    return 1 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
