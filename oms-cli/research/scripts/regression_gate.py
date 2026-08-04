#!/usr/bin/env python3
"""The regression gate — run this BEFORE trusting a newly assembled spec.

    for every endpoint in the PREVIOUS spec but not the new one:
        require a positive justification:
          proven dead (404/5xx) | proven unsafe (verdict) | explicitly superseded
        otherwise -> BUG, not a result

A regeneration that silently ships fewer working commands is a regression
wearing a growth number: "73 -> 140 endpoints" reads like a win even while it
quietly drops eleven commands somebody's script depends on. On the factory run
this gate caught three separate pipeline bugs that every safety check had
already passed — refutations being treated as deletions (28 working commands),
prose keyword-matching that killed a live endpoint, and a "write-only" drop of
four endpoints the server actually served GET on.

It also enforces skill rule 6 in the other direction: an endpoint that survives
must keep its shipped `resource endpoint` command name. A rename is as breaking
as a deletion — worse, because it looks like the command still exists — and MCP
`endpoint_id`s (`hana.product-stock`) are a public contract that agent
workflows reference by string.

Justifications live in JUSTIFIED_DROPS below, in code, each with the evidence
that earned it. A drop with no entry here fails the gate. Deliberately: the
cost of a false alarm is one line of typing, and the cost of a miss is an
operator whose command vanished with no way to tell whether it was on purpose.

usage: regression_gate.py <old-spec.yaml> <new-spec.yaml>
exit 0 = clean, 1 = regression
"""
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from normalise import norm  # noqa: E402

# path -> (reason_class, evidence). reason_class must be one of:
#   proven-dead | proven-unsafe | superseded
JUSTIFIED_DROPS = {
    # (populated only if the assembler genuinely needs to drop something;
    #  the OMS run's design goal is an EMPTY dict — every shipped endpoint
    #  carried forward, including the three that are broken upstream, because
    #  "broken upstream today" is not "dead" and they must reappear the day
    #  the OMS team fixes them.)
}


def parse(spec_path):
    """normalised path -> 'resource endpoint'. Deliberately ignores the
    `config:` block: a carry-forward regex on the ecom run scraped it and
    published `~/.config/<cli>/config.toml` as an API endpoint under a `~`
    resource."""
    txt = open(spec_path).read()
    out, res, ep = {}, None, None
    in_resources = False
    for line in txt.split("\n"):
        if re.match(r"^resources:\s*$", line):
            in_resources = True
            continue
        if in_resources and re.match(r"^\S", line):
            in_resources = False
        if not in_resources:
            continue
        m = re.match(r"^  ([\w-]+):\s*$", line)
        if m:
            res, ep = m.group(1), None
            continue
        m = re.match(r"^      ([\w-]+):\s*$", line)
        if m:
            ep = m.group(1)
            continue
        m = re.match(r'^\s+path: "([^"]+)"', line)
        if m and res and ep and m.group(1).startswith("/api"):
            out[norm(m.group(1))] = f"{res} {ep}"
    return out


def main():
    old, new = parse(sys.argv[1]), parse(sys.argv[2])
    fail = 0

    dropped = sorted(set(old) - set(new))
    print(f"== dropped vs previous spec: {len(dropped)} ==")
    for p in dropped:
        j = JUSTIFIED_DROPS.get(p)
        if j:
            print(f"  ok   {p:48} [{j[0]}] {j[1]}")
        else:
            print(f"  BUG  {p:48} was `{old[p]}` — dropped with NO justification")
            fail += 1

    renamed = [(p, old[p], new[p]) for p in sorted(set(old) & set(new)) if old[p] != new[p]]
    print(f"\n== renamed commands (skill rule 6 — must be zero): {len(renamed)} ==")
    for p, o, n in renamed:
        print(f"  BUG  {p:48} `{o}` -> `{n}`")
        fail += 1

    added = sorted(set(new) - set(old))
    print(f"\n== added: {len(added)} ==")
    for p in added:
        print(f"  new  {p:48} `{new[p]}`")

    print(f"\nprevious: {len(old)}   new: {len(new)}   "
          f"carried: {len(set(old) & set(new))}   added: {len(added)}   dropped: {len(dropped)}")

    if fail:
        print(f"\nGATE FAILED: {fail} unexplained regression(s). "
              f"This is a BUG in the pipeline, not a result.")
        return 1
    print("\nGATE PASSED: no unexplained drops, no renames.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
