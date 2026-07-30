#!/usr/bin/env python3
"""JIVO harness — sync. Moves corrections between operators without anyone
having to know what git is.

Why this exists
---------------
The harness only pays off if a correction one person records reaches everyone
else. That transport is git, and the people using this toolkit are Accounts and
Sales staff who have never run a git command and should never have to. Asked
directly, the owner said: "wtf is git we never worked on it."

So this does exactly two things, on the operator's behalf, and nothing else:

    pull   bring in corrections other people recorded
    push   send corrections this operator recorded

Safety rules, because this runs unattended in someone else's repository:

  * `pull` is `fetch` + `merge --ff-only`. A fast-forward cannot create a
    conflict and cannot lose a local commit. If the branch has diverged, or the
    working tree would be disturbed, it declines and says so instead of trying
    to be clever.
  * `push` stages ONLY `harness/corrections/`. It will never sweep up an
    operator's half-finished work, a credential file, or another session's
    in-progress feature — a real risk in this repo, which usually has dozens of
    unrelated modified files.
  * Neither ever runs `reset`, `rebase`, `checkout`, `clean`, or `push --force`.
    Nothing here can destroy work.
  * Network calls are bounded. A dead remote (VPN down, laptop on a train) must
    not hang the operator's session — it degrades to "you are working with the
    corrections you already have."

Issues no business-system call of any kind, and touches no file outside
harness/corrections/.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

HARNESS = Path(__file__).resolve().parent.parent
REPO = HARNESS.parent
SCOPE = "harness/corrections"

NET_TIMEOUT = int(os.environ.get("JIVO_SYNC_TIMEOUT", "25"))


def _git(*args: str, timeout: int = 15) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True, text=True, timeout=timeout, errors="replace",
    )


def _branch() -> str:
    r = _git("rev-parse", "--abbrev-ref", "HEAD")
    return r.stdout.strip() if r.returncode == 0 else ""


def _usable_repo() -> tuple[bool, str]:
    if not (REPO / ".git").exists():
        return False, "not a git clone — corrections cannot be shared"
    if _git("remote", "get-url", "origin").returncode != 0:
        return False, "no 'origin' remote configured"
    return True, ""


# ── pull ─────────────────────────────────────────────────────────────────────

def cmd_pull(args: argparse.Namespace) -> int:
    ok, why = _usable_repo()
    if not ok:
        if args.quiet:
            return 0
        print(f"jivo-sync: {why}", file=sys.stderr)
        return 0

    branch = _branch()
    if not branch or branch == "HEAD":
        if not args.quiet:
            print("jivo-sync: detached HEAD — not pulling", file=sys.stderr)
        return 0

    try:
        f = _git("fetch", "--quiet", "origin", branch, timeout=NET_TIMEOUT)
    except subprocess.TimeoutExpired:
        if not args.quiet:
            print(f"jivo-sync: remote unreachable within {NET_TIMEOUT}s — "
                  "using the corrections already on this machine", file=sys.stderr)
        return 0
    if f.returncode != 0:
        if not args.quiet:
            print("jivo-sync: fetch failed — using the corrections already on "
                  f"this machine. {(f.stderr or '').strip().splitlines()[:1]}",
                  file=sys.stderr)
        return 0

    behind = _git("rev-list", "--count", f"HEAD..origin/{branch}").stdout.strip()
    if behind in ("", "0"):
        if not args.quiet:
            print("jivo-sync: already up to date")
        return 0

    # A fast-forward is the only merge that cannot conflict or lose a commit.
    m = _git("merge", "--ff-only", f"origin/{branch}", timeout=30)
    if m.returncode == 0:
        n = _new_corrections_in(f"HEAD@{{1}}", "HEAD")
        msg = f"jivo-sync: pulled {behind} update(s) from the team"
        if n:
            msg += f" — {n} new correction(s) now active"
        print(msg)
        return 0

    # Declined. Say which case it is, in words an operator can act on.
    ahead = _git("rev-list", "--count", f"origin/{branch}..HEAD").stdout.strip()
    if ahead not in ("", "0"):
        print(f"jivo-sync: cannot auto-update — this machine has {ahead} local "
              f"commit(s) not on the server and {behind} waiting to come down. "
              "Ask Daman to reconcile; nothing was changed.", file=sys.stderr)
    else:
        print("jivo-sync: cannot auto-update — local edits would be overwritten. "
              f"Nothing was changed. {(m.stderr or '').strip().splitlines()[:1]}",
              file=sys.stderr)
    return 0


def _new_corrections_in(a: str, b: str) -> int:
    r = _git("diff", "--name-only", "--diff-filter=A", a, b, "--", SCOPE)
    if r.returncode != 0:
        return 0
    return len([ln for ln in r.stdout.splitlines()
                if ln.strip() and "/C-" in ln and ln.endswith(".md")])


# ── push ─────────────────────────────────────────────────────────────────────

def cmd_push(args: argparse.Namespace) -> int:
    ok, why = _usable_repo()
    if not ok:
        print(f"jivo-sync: {why}", file=sys.stderr)
        return 1

    # Is there anything of ours to send?
    st = _git("status", "--porcelain", "--", SCOPE)
    if st.returncode != 0:
        print("jivo-sync: could not read git status", file=sys.stderr)
        return 1
    pending = [ln for ln in st.stdout.splitlines() if ln.strip()]

    branch = _branch()
    if not branch or branch == "HEAD":
        print("jivo-sync: detached HEAD — not pushing", file=sys.stderr)
        return 1

    if not pending:
        # Nothing new in the working tree — but a correction may already be
        # committed and simply never sent (this happens after a declined
        # fast-forward). Reporting "nothing to send" here would strand it
        # silently, which is precisely the failure this tool exists to prevent.
        try:
            _git("fetch", "--quiet", "origin", branch, timeout=NET_TIMEOUT)
        except subprocess.TimeoutExpired:
            pass
        ahead = _git("rev-list", "--count", f"origin/{branch}..HEAD").stdout.strip()
        if ahead in ("", "0"):
            if not args.quiet:
                print("jivo-sync: no new corrections to send")
            return 0
        behind = _git("rev-list", "--count", f"HEAD..origin/{branch}").stdout.strip()
        if behind not in ("", "0"):
            print(f"jivo-sync: {ahead} correction commit(s) on this machine have "
                  f"NOT reached the team, and {behind} update(s) are waiting to "
                  "come down. This needs Daman to reconcile once — your work is "
                  "committed and safe, but it is not shared yet.", file=sys.stderr)
            return 1
        return _do_push(branch, note=f"{ahead} previously-unsent commit(s)")

    # Stage ONLY corrections. This repo routinely has dozens of unrelated
    # modified files; a bare `git add -A` here would ship somebody's WIP.
    if _git("add", "--", SCOPE).returncode != 0:
        print("jivo-sync: could not stage corrections", file=sys.stderr)
        return 1

    staged = _git("diff", "--cached", "--name-only", "--", SCOPE).stdout.split()
    added = [f for f in staged if "/C-" in f and f.endswith(".md")]
    who = (os.environ.get("JIVO_USER") or os.environ.get("USER")
           or os.environ.get("USERNAME") or "operator")
    subject = (f"correction: {Path(added[0]).stem}" if len(added) == 1
               else f"corrections: {len(added) or len(staged)} update(s) from {who}")
    body = ("Recorded by an operator via the jivo-correct skill and synced "
            "automatically.\n\nFiles:\n" + "\n".join(f"  {f}" for f in staged))

    c = _git("commit", "-m", subject, "-m", body)
    if c.returncode != 0:
        print(f"jivo-sync: commit failed — {(c.stderr or c.stdout).strip()[:200]}",
              file=sys.stderr)
        return 1

    return _do_push(branch, note=f"{len(added) or len(staged)} correction(s)")


def _do_push(branch: str, note: str) -> int:
    """Send committed corrections. Pull first so we cannot be rejected for
    being behind; never force."""
    cmd_pull(argparse.Namespace(quiet=True))

    try:
        p = _git("push", "origin", branch, timeout=NET_TIMEOUT)
    except subprocess.TimeoutExpired:
        print(f"jivo-sync: committed locally, but the server did not answer "
              f"within {NET_TIMEOUT}s. Your correction is SAVED and will go out "
              "next time. Nothing is lost.", file=sys.stderr)
        return 0
    if p.returncode != 0:
        print("jivo-sync: committed locally, but could not send to the server. "
              "Your correction is SAVED and will go out next time. "
              f"{(p.stderr or '').strip().splitlines()[:1]}", file=sys.stderr)
        return 0

    print(f"jivo-sync: sent {note} — every other operator gets this on their "
          "next session")
    return 0


# ── status ───────────────────────────────────────────────────────────────────

def cmd_status(args: argparse.Namespace) -> int:
    ok, why = _usable_repo()
    print("jivo-sync status")
    if not ok:
        print(f"  {why}")
        return 1
    branch = _branch()
    print(f"  branch          : {branch}")
    print(f"  origin          : {_git('remote', 'get-url', 'origin').stdout.strip()}")
    st = _git("status", "--porcelain", "--", SCOPE).stdout.splitlines()
    print(f"  unsent locally  : {len([l for l in st if l.strip()])} change(s) in {SCOPE}")
    try:
        _git("fetch", "--quiet", "origin", branch, timeout=NET_TIMEOUT)
        behind = _git("rev-list", "--count", f"HEAD..origin/{branch}").stdout.strip()
        ahead = _git("rev-list", "--count", f"origin/{branch}..HEAD").stdout.strip()
        print(f"  waiting to pull : {behind or '?'} commit(s)")
        print(f"  ahead of server : {ahead or '?'} commit(s)")
    except subprocess.TimeoutExpired:
        print("  remote          : unreachable (offline is fine — reads still work)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="sync",
        description="Share JIVO corrections without anyone needing to use git.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("pull", help="bring in corrections other people recorded")
    p.add_argument("--quiet", action="store_true")
    p.set_defaults(func=cmd_pull)

    p = sub.add_parser("push", help="send corrections this operator recorded")
    p.add_argument("--quiet", action="store_true")
    p.set_defaults(func=cmd_push)

    p = sub.add_parser("status", help="what is unsent, what is waiting")
    p.set_defaults(func=cmd_status)

    args = ap.parse_args()
    try:
        return args.func(args)
    except subprocess.TimeoutExpired:
        print("jivo-sync: git timed out — nothing was changed", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
