#!/usr/bin/env python3
"""Parse the six phase-3 domain studies into a structured overlay.

The studies are markdown written to STUDY-CONTRACT.md's shape:

    ### `/api/hana/batch-details/`
    - **command**: `hana batch-details`
    - **verdict**: publish
    - **description**: ...
    - **params**:
      - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: ...
    - **response**: `array`. Keys: ...

This reads that back out. It is deliberately strict: an endpoint block whose
`command` or `verdict` cannot be read is reported, not silently skipped. A
parser that quietly drops an endpoint produces a spec that is missing a command
with no error anywhere — the exact failure the regression gate exists to catch,
except arriving one stage earlier where the gate cannot see it.

usage: parse_studies.py <studies-dir> > overlay.json
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from normalise import norm  # noqa: E402

# The path, then anything. Studies annotate the heading -
#     ### `/api/orders/flow-config/`  *(dual-verb: GET + POST - GET only)*
# and anchoring on end-of-line missed every annotated heading. Worse than
# missing them: parsing then RAN ON from the previous endpoint into the next
# one's fields, so `/api/orders/list/` came out carrying the command name and
# verdict of `/api/orders/notifications/` - a publish silently turned into an
# exclude. A parser that mis-attributes is more dangerous than one that skips,
# because the count still looks plausible.
H3 = re.compile(r"^#{3}\s+`([^`]+)`")
FIELD = re.compile(r"^-\s+\*\*([\w ]+)\*\*:\s*(.*)$")
# - `branch` — string, required, not positional. `OIL | BEVERAGE`. Source: ...
PARAM = re.compile(r"^\s+-\s+`([A-Za-z_][\w]*)`\s*[—-]\s*(.*)$")


def parse_param(name, rest):
    p = {"name": name}
    low = rest.lower()
    p["type"] = ("int" if re.search(r"\bint(eger)?\b", low)
                 else "bool" if re.search(r"\bbool(ean)?\b", low)
                 else "string")
    # "required" but not "not required" / "optional"
    p["required"] = bool(re.search(r"\brequired\b", low)) and not re.search(
        r"\b(not required|optional)\b", low)
    p["positional"] = bool(re.search(r"\bpositional\b", low)) and not re.search(
        r"\bnot positional\b", low)
    # enum: first backticked run containing a pipe, e.g. `OIL | BEVERAGE`
    m = re.search(r"`([A-Z0-9_]+(?:\s*\|\s*[A-Z0-9_]+)+)`", rest)
    if m:
        p["enum"] = [x.strip() for x in m.group(1).split("|")]
    p["note"] = re.sub(r"\s+", " ", rest).strip()
    return p


def parse_file(path):
    out, cur, field, buf = [], None, None, []

    def flush_field():
        nonlocal field, buf
        if cur and field:
            cur.setdefault("_raw", {})[field] = "\n".join(buf).strip()
        field, buf = None, []

    for line in open(path):
        line = line.rstrip("\n")
        m = H3.match(line)
        if m:
            flush_field()
            cur = {"path": norm(m.group(1)), "raw_path": m.group(1),
                   "source": os.path.basename(path), "params": []}
            out.append(cur)
            continue
        if cur is None:
            continue
        m = FIELD.match(line)
        if m:
            flush_field()
            field = m.group(1).strip().lower()
            buf = [m.group(2)]
            continue
        if field == "params":
            m = PARAM.match(line)
            if m:
                cur["params"].append(parse_param(m.group(1), m.group(2)))
                continue
        if field and (line.startswith("  ") or line.startswith("\t")):
            buf.append(line.strip())
            continue
        if line.startswith("#") or (line and not line.startswith(("-", " ", "\t"))):
            flush_field()
    flush_field()

    for e in out:
        raw = e.pop("_raw", {})
        cmd = raw.get("command", "")
        m = re.search(r"`([\w-]+)\s+([\w-]+)`", cmd)
        e["resource"], e["command"] = (m.group(1), m.group(2)) if m else (None, None)
        # Read the LEADING token, never a substring-anywhere test.
        #
        # Dual-verb URLs are written as
        #     - **verdict**: publish (GET). The `POST` on this same URL is excluded
        # and a substring test for "exclude" turns that publish into an exclude.
        # It silently dropped `orders flow-config`, `orders notifications`,
        # `orders staff-products` and `orders party-flow-config` - four SHIPPED,
        # working commands - while the endpoint count still looked healthy.
        # Leading emphasis (`**exclude**`) and trailing prose are stripped first.
        v = raw.get("verdict", "").lower().lstrip("* \t")
        m2 = re.match(r"(publish|exclude)", v)
        e["verdict"] = m2.group(1) if m2 else None
        e["exclusion_reason"] = re.sub(r"\s+", " ", raw.get("exclusion reason", "")).strip()
        d = re.sub(r"\s+", " ", raw.get("description", "")).strip()
        e["description"] = d
        r = raw.get("response", "")
        e["response_type"] = ("array" if re.match(r"^\s*`?array", r, re.I)
                              else "object" if re.match(r"^\s*`?object", r, re.I)
                              else None)
        e["response_unverified"] = "UNVERIFIED" in r.upper()
        e["traps"] = re.sub(r"\s+", " ", raw.get("traps", "")).strip()
    return out


def main():
    entries, problems = [], []
    for f in sorted(glob.glob(os.path.join(sys.argv[1], "study-*.md"))):
        got = parse_file(f)
        for e in got:
            if not e["verdict"]:
                problems.append(f"{e['source']} {e['path']}: no verdict parsed")
            if e["verdict"] == "publish" and not e["command"]:
                problems.append(f"{e['source']} {e['path']}: publish with no command name")
        entries.extend(got)
        print(f"  {os.path.basename(f)}: {len(got)} endpoints", file=sys.stderr)

    seen = {}
    for e in entries:
        if e["path"] in seen and seen[e["path"]]["source"] != e["source"]:
            problems.append(f"{e['path']} claimed by two studies: "
                            f"{seen[e['path']]['source']} and {e['source']}")
        seen[e["path"]] = e

    pub = [e for e in entries if e["verdict"] == "publish"]
    exc = [e for e in entries if e["verdict"] == "exclude"]
    print(f"\n  total {len(entries)}  publish {len(pub)}  exclude {len(exc)}",
          file=sys.stderr)
    if problems:
        print("\n  PARSE PROBLEMS (fix before emitting):", file=sys.stderr)
        for p in problems:
            print("   ", p, file=sys.stderr)
    json.dump({"entries": entries, "problems": problems}, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
