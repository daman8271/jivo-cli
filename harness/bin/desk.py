#!/usr/bin/env python3
"""desk.py — keep a box from carrying skills its desk must not have.

Every operator box fast-forwards the whole of `main` at session start, so a
skill folder committed there lands on every desk. `harness/desks.json` names
the boxes that must NOT carry a given set of skill folders; this script hides
those folders with `git sparse-checkout`, which survives every future pull.

    python3 harness/bin/desk.py apply [--quiet]   # run by the SessionStart hook
    python3 harness/bin/desk.py show              # what this box matches

Identity is matched case-insensitively as a substring against: the hostname,
%COMPUTERNAME%, the local username, and the slug/name in harness/.operator.
`JIVO_DESK_AS=<name>` overrides all of them (testing only).

A box that matches nothing is never touched — unless it still carries a block
this script wrote earlier, which is then removed. Other sparse-checkout
patterns a clone already has (Preshit's sparse clone) are preserved verbatim.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent
REPO = HARNESS.parent
DESKS = HARNESS / "desks.json"
BEGIN = "# jivo-desk begin (managed by harness/bin/desk.py — edit harness/desks.json instead)"
END = "# jivo-desk end"


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True,
                          errors="replace", timeout=30)


def _identity() -> list[str]:
    forced = os.environ.get("JIVO_DESK_AS")
    if forced:
        return [forced]
    ids: list[str] = []
    for v in (socket.gethostname(), os.environ.get("COMPUTERNAME", "")):
        if v:
            ids.append(v)
    try:
        ids.append(getpass.getuser())
    except Exception:
        pass
    op = HARNESS / ".operator"
    if op.exists():
        try:
            d = json.loads(op.read_text(encoding="utf-8"))
            ids += [str(d.get(k, "")) for k in ("slug", "name") if d.get(k)]
        except Exception:
            pass
    return [i for i in ids if i]


def _excluded_paths(identity: list[str]) -> tuple[list[str], list[str]]:
    """Returns (paths to hide, notes of the matching rules)."""
    if not DESKS.exists():
        return [], []
    cfg = json.loads(DESKS.read_text(encoding="utf-8"))
    sets = cfg.get("skill_sets", {})
    low = [i.lower() for i in identity]
    paths: list[str] = []
    notes: list[str] = []
    for rule in cfg.get("exclude", []):
        tokens = [str(t).lower() for t in rule.get("who", [])]
        if not any(tok and tok in ident for tok in tokens for ident in low):
            continue
        notes.append(rule.get("note", ",".join(tokens)))
        for s in rule.get("sets", []):
            paths += sets.get(s, [])
        paths += rule.get("paths", [])
    seen: dict[str, None] = {}
    for p in paths:
        seen[p.strip("/")] = None
    return list(seen), notes


def drafts_only_note(identity: list[str]) -> str | None:
    """The note on this box's drafts-only rule, or None.

    `sapb1` enforces this rule itself (sap-b1/cli/internal/config/desk.go reads
    the same list) — this is only how the AI in the session gets TOLD, so it
    stops at the draft instead of discovering the refusal by running into it.
    Best-effort: a broken desks.json must never take out SessionStart.
    """
    if not DESKS.exists():
        return None
    try:
        cfg = json.loads(DESKS.read_text(encoding="utf-8"))
    except Exception:
        return None
    low = [i.lower() for i in identity]
    for rule in cfg.get("drafts_only", []):
        tokens = [str(t).lower() for t in rule.get("who", [])]
        if any(tok and tok in ident for tok in tokens for ident in low):
            return rule.get("note") or ", ".join(tokens)
    return None


# ASCII ONLY, deliberately. A Windows console is cp1252: one arrow or em dash
# raises UnicodeEncodeError inside print(), main()'s catch-all swallows it, and
# the banner silently does not reach the session — which is the whole point of
# the banner. Caught live on PC-AUDIT-05, 2026-09-03.
POLICY_BANNER = """## THIS DESK NEVER REACHES THE APPROVER - stop at the draft

{note}

### A GRPO is a DRAFT here too. Never post one live. - Daman 2026-09-08

*"we will be making drafts for each ok i repeat do not post directly pls get
tht in ur mind"*.

- Build it with `sapb1 draft grpo` - `--dry-run`, the operator okays the shape,
  then `--yes`. Never `sapb1 post PurchaseDeliveryNotes`, even though the CLI
  still permits it for a GRPO and only a GRPO.
- A live GRPO is in the books instantly: stock moves, the ledger moves, there
  is no approver, and NOTHING in this CLI can undo it - only a person in the
  SAP B1 client can reverse it, and that adds a reversal document rather than
  removing anything.
- If a book refuses the draft (the old `-6006 Modifying this object is not
  permitted for current user`), **stop and say so.** Do not fall back to the
  live post to get the job done. The fallback is a login that can draft in that
  book, or a person keying it in the SAP B1 client.
- This supersedes the 2026-09-04 live-post route that used to be printed here.
  Its premise is gone twice over: Daman turned live posting off on 09-08, and
  USER19 can draft in JIVO_MART again as of 09-08 (drafts 40246-59).

### Everything else: build the draft and STOP - you never press Add

- Do NOT run `sapb1 add-draft`. The binary refuses it here and exits 9; that
  refusal IS the policy, not a fault to route around. It is what keeps this
  desk's work out of the approver's queue.
- Do NOT reach for `post`, `patch`, curl, another checkout or another login to
  get the same effect. There is no flag and no second route.
- `post` still refuses every posting document in code - A/P and A/R invoices,
  credit notes, orders, payments, journal entries, stock movements - with no
  override.
- Submitting a draft for approval, and posting an approved one, are this
  operator's own clicks in the SAP B1 client: Document Drafts -> open it -> Add.
- CLAUDE.md's "a bill is not done at the draft - send it to the approver" rule
  does NOT apply on this desk. Here the bill is done when the draft exists and
  the operator has been told its number."""


def _say(text: str) -> None:
    """print() that cannot die on a cp1252 console — see POLICY_BANNER."""
    enc = (sys.stdout.encoding or "utf-8")
    sys.stdout.write(text.encode(enc, "replace").decode(enc, "replace") + "\n")


def cmd_policy(args: argparse.Namespace) -> int:
    note = drafts_only_note(_identity())
    if not note:
        return 0
    _say(POLICY_BANNER.format(note=note))
    return 0


def _sparse_file() -> Path:
    r = _git("rev-parse", "--git-path", "info/sparse-checkout")
    rel = (r.stdout or "").strip() or ".git/info/sparse-checkout"
    p = Path(rel)
    return p if p.is_absolute() else REPO / p


def _strip_block(lines: list[str]) -> list[str]:
    out, skipping = [], False
    for ln in lines:
        if ln.strip() == BEGIN:
            skipping = True
            continue
        if ln.strip() == END:
            skipping = False
            continue
        if not skipping:
            out.append(ln)
    return [ln for ln in out if ln.strip()]


def cmd_apply(args: argparse.Namespace) -> int:
    if _git("rev-parse", "--is-inside-work-tree").stdout.strip() != "true":
        return 0
    identity = _identity()
    paths, notes = _excluded_paths(identity)
    sf = _sparse_file()
    existing = sf.read_text(encoding="utf-8").splitlines() if sf.exists() else []
    had_block = any(ln.strip() == BEGIN for ln in existing)
    base = _strip_block(existing)

    if not paths:
        if not had_block:
            return 0  # not our box, never written to — leave it alone
        # Rule was lifted: drop our block, restore the folders.
        if base:
            sf.write_text("\n".join(base) + "\n", encoding="utf-8")
            _git("sparse-checkout", "reapply")
        else:
            _git("sparse-checkout", "disable")
        if not args.quiet:
            print("jivo-desk: exclusions lifted, all skills restored")
        return 0

    if not base:
        base = ["/*"]
    # No trailing slash: "!/x/" matches only a directory, so a single file
    # (another operator's .env) stayed on the box. "!/x" matches both.
    block = [BEGIN, *[f"!/{p}" for p in paths], END]
    content = "\n".join(base + block) + "\n"
    still_present = [p for p in paths if (REPO / p).exists()]
    if sf.exists() and sf.read_text(encoding="utf-8") == content and not still_present:
        return 0  # already applied, nothing on disk to remove

    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(content, encoding="utf-8")
    _git("config", "core.sparseCheckout", "true")
    _git("config", "core.sparseCheckoutCone", "false")
    # `git clone --sparse` stores these in the worktree config, which shadows
    # the repo config — set it there too or cone mode silently stays on.
    if _git("config", "core.sparseCheckoutCone").stdout.strip() != "false":
        _git("config", "--worktree", "core.sparseCheckout", "true")
        _git("config", "--worktree", "core.sparseCheckoutCone", "false")
    r = _git("sparse-checkout", "reapply")
    if r.returncode != 0:
        r = _git("read-tree", "-mu", "HEAD")
    left = [p for p in paths if (REPO / p).exists()]
    if not args.quiet or left:
        who = "; ".join(notes)
        print(f"jivo-desk: this box does not carry {len(paths)} skill folder(s) ({who})")
        if left:
            print(f"jivo-desk: WARNING could not remove: {', '.join(left)} — "
                  f"{(r.stderr or r.stdout).strip()[:200]}", file=sys.stderr)
            return 1
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    identity = _identity()
    paths, notes = _excluded_paths(identity)
    print("identity:", ", ".join(identity))
    note = drafts_only_note(identity)
    _say("drafts-only: " + (f"YES - {note}" if note else "no (this desk may press Add)"))
    if not paths:
        print("no exclusions — this box carries every skill on main")
        return 0
    print("rules:", "; ".join(notes))
    for p in paths:
        print(f"  {'HIDDEN ' if not (REPO / p).exists() else 'PRESENT'} {p}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("apply", help="hide the skill folders this box must not carry")
    a.add_argument("--quiet", action="store_true")
    a.set_defaults(fn=cmd_apply)
    pol = sub.add_parser("policy", help="print this box's drafts-only banner, if it has one")
    pol.set_defaults(fn=cmd_policy)
    s = sub.add_parser("show", help="what this box matches")
    s.set_defaults(fn=cmd_show)
    args = ap.parse_args()
    try:
        return args.fn(args)
    except Exception as e:  # never break a session start
        print(f"jivo-desk: skipped ({e})", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
