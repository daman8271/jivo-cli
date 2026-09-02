#!/usr/bin/env python3
"""history.py — append one point per publish to site-v2/data/history.jsonl.

v1 kept no history at all, so nothing on the board could trend and no one could
answer "is this worse than yesterday?". That is a large amount of value for a
very small file: one line per publish, deduped to at most one every 30 minutes,
gives every KPI card a sparkline and every headline a "moved since yesterday".

It is append-only and never rewritten, so a corrupt or partial line costs one
point, never the series. Readers skip lines that do not parse.

  python3 pipeline/history.py [--data site-v2/data] [--min-gap-min 30] [--keep 4000]
"""
import argparse, datetime, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def last_point(path):
    """Read only the tail — the file grows forever and we need one line."""
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        try:
            fh.seek(-8192, os.SEEK_END)
        except OSError:
            fh.seek(0)
        tail = fh.read().decode("utf-8", "replace").splitlines()
    for line in reversed(tail):
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue          # a torn line costs one point, not the series
    return None


def _stamp_count(man_path, man, n):
    """Write history_points back into the manifest, atomically."""
    man["history_points"] = n
    tmp = man_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1, sort_keys=True)
    os.replace(tmp, man_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=os.path.join(ROOT, "site-v2", "data"))
    ap.add_argument("--min-gap-min", type=int, default=30)
    ap.add_argument("--keep", type=int, default=4000)
    a = ap.parse_args()

    man_path = os.path.join(a.data, "manifest.json")
    if not os.path.exists(man_path):
        print("history: no manifest at %s — nothing to record" % man_path, file=sys.stderr)
        return 1
    man = load(man_path)

    gen = man.get("generated_at")
    if not gen:
        print("history: manifest has no generated_at", file=sys.stderr)
        return 1

    hist = os.path.join(a.data, "history.jsonl")
    prev = last_point(hist)

    # last_point reads only the tail, which is enough to skip an immediate repeat
    # but not a stamp that reappears after other writes — 17 lines had accumulated
    # for 2 distinct builds. Scan the stamps already recorded and never write one
    # twice; the file stays append-only and one pass over a few thousand short
    # lines costs nothing next to a 40-second SAP build.
    seen = set()
    if os.path.exists(hist):
        with open(hist, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    seen.add(json.loads(line).get("t"))
                except json.JSONDecodeError:
                    continue
    if gen in seen:
        # Still publish the count: returning early used to leave history_points
        # at 0, so the board reported "no history" on every tick that did not
        # add a point — which is most of them.
        _stamp_count(man_path, man, len(seen))
        print("history: %s already recorded (%d points)" % (gen, len(seen)))
        return 0

    # Dedupe on the BUILD stamp, not on wall clock: two ticks of the same build
    # are the same fact, and at a 2-minute cadence that is most of them.
    if prev and prev.get("t") == gen:
        print("history: already recorded %s" % gen)
        return 0
    if prev and prev.get("t"):
        try:
            gap = (datetime.datetime.fromisoformat(gen)
                   - datetime.datetime.fromisoformat(prev["t"])).total_seconds() / 60.0
            if 0 <= gap < a.min_gap_min:
                print("history: last point %.1f min ago (< %d) — skipping"
                      % (gap, a.min_gap_min))
                return 0
        except ValueError:
            pass              # unparseable previous stamp: record anyway

    point = {
        "t": gen,
        "as_of": man.get("as_of"),
        "kpis": {co: {k: v.get("value") for k, v in kd.items()}
                 for co, kd in (man.get("kpis") or {}).items()},
        "rows": {sec: (meta.get("rows") or {})
                 for sec, meta in (man.get("sections") or {}).items()},
        "build_seconds": man.get("build_seconds"),
        "stale": bool(man.get("stale")),
    }

    os.makedirs(a.data, exist_ok=True)
    with open(hist, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(point, sort_keys=True, separators=(",", ":")) + "\n")

    # Trim from the front only when it has really grown; rewriting is the one
    # risky operation here, so do it rarely and atomically.
    with open(hist, encoding="utf-8") as fh:
        lines = fh.readlines()
    if len(lines) > a.keep * 1.25:
        tmp = hist + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.writelines(lines[-a.keep:])
        os.replace(tmp, hist)
        lines = lines[-a.keep:]

    man["history_points"] = len(lines)
    tmp = man_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1, sort_keys=True)
    os.replace(tmp, man_path)

    print("history: recorded %s (%d points)" % (gen, len(lines)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
