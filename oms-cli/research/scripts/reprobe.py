#!/usr/bin/env python3
"""Serial retry pass for OMS probe records that failed to CONNECT (http == 0).

Skill rule 3: a failure to measure is not a measurement. Concurrent probing on
factory produced 385 connection refusals that looked exactly like "endpoint
absent" in a status column, and the first aggregate computed from them claimed
zero endpoints existed. `http: 0` is deliberately kept structurally distinct
from every HTTP status so those records can be found and retried here, serially,
before any aggregate is computed.

usage: reprobe.py <jsonl>    (rewrites in place)
"""
import json
import sys
import time
from collections import Counter

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from probe import probe  # noqa: E402  same transport, same headers, same safety

path_jsonl = sys.argv[1]
recs = [json.loads(l) for l in open(path_jsonl)]
todo = [r for r in recs if r.get("http") == 0]
print(f"{len(todo)} transport failures to retry (serial, 3 attempts)", flush=True)

fixed = 0
for i, r in enumerate(todo):
    for attempt in range(3):
        new = probe(r["path"], r.get("branch") or "")
        if new["http"] != 0:
            r.clear()
            r.update(new)
            fixed += 1
            break
        time.sleep(2.0 * (attempt + 1))
    time.sleep(0.2)
    if (i + 1) % 10 == 0:
        print(f"  {i+1}/{len(todo)} retried, {fixed} recovered", flush=True)

with open(path_jsonl, "w") as f:
    for r in sorted(recs, key=lambda r: (r["path"], r.get("branch", ""))):
        f.write(json.dumps(r) + "\n")

still = sum(1 for r in recs if r.get("http") == 0)
print(f"\nrecovered {fixed}/{len(todo)}; still unreachable: {still}")
for k, v in sorted(Counter(f'{r.get("branch") or "-"}:{r["http"]}' for r in recs).items()):
    print(f"  {k:22} {v}")
if still:
    print("\nWARNING: still-unreachable paths are UNMEASURED, not absent. "
          "Do not let them fall into a 'dead' bucket.")
