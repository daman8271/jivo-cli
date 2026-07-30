#!/usr/bin/env python3
"""JIVO harness — sync. Moves work between operators without anyone having to
know what git is.

Why this exists
---------------
The harness only pays off if a correction one person records reaches everyone
else. That transport is git, and the people using this toolkit are Accounts and
Sales staff who have never run a git command and should never have to. Asked
directly, the owner said: "wtf is git we never worked on it."

So this does these things on the operator's behalf, and nothing else:

    pull   bring in what other people recorded
    push   send what this operator recorded
    daily  once a day: repair the shared rules, then pull and push

It carries corrections AND this operator's own session log (chats/<name>/,
queries/<name>/). It used to carry only corrections, which was right when only
corrections moved — but operators now write a session note every day, and a
transport that ignored those left them stranded on the laptop.

Safety rules, because this runs unattended in someone else's repository:

  * `pull` tries `merge --ff-only` first, because a fast-forward cannot conflict
    and cannot lose a commit. Only if the branch has genuinely DIVERGED does it
    fall back to `pull --rebase --autostash`, which replays this operator's
    commits on top and puts back any uncommitted work afterwards.

    ff-only alone is not enough any more, and that is worth spelling out: once
    every operator commits a session note daily, every laptop is permanently
    ahead of the server, so a diverged branch is the NORMAL state rather than
    the exception. ff-only would then decline on every single session and
    corrections would quietly stop arriving — no error, no warning, just a team
    that slowly falls out of sync. --autostash matters for the same reason:
    plain `pull --rebase` refuses outright when the tree has ANY unstaged
    change, in any file, and a non-technical operator always has one.
  * `push` stages ONLY `harness/corrections/` and this operator's own
    `chats/<name>/` + `queries/<name>/`. It will never sweep up someone's
    half-finished work, a credential file, or another session's in-progress
    feature — a real risk in this repo, which usually has dozens of unrelated
    modified files.
  * `daily` also restores the protected files listed in
    harness/protected.manifest, discarding local edits to them ONLY. That list
    is explicit and closed; `git checkout --` is never given a directory, a
    glob, or `.`.
  * NEVER `reset --hard`, NEVER `clean`, NEVER `push --force`. Nothing here can
    destroy work: a rebase that cannot proceed is aborted and left as it was,
    and an autostash that cannot re-apply leaves the work in the stash.
  * Network calls are bounded. A dead remote (VPN down, laptop on a train) must
    not hang the operator's session — it degrades to "you are working with the
    corrections you already have."

Issues no business-system call of any kind.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
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

# The team's shared truths. Always in scope.
SCOPE = "harness/corrections"

# Files that decide how every operator's Claude behaves. `daily` restores these
# from the last commit, discarding local edits. Kept in step with
# guard.py's PROTECTED list.
PROTECTED = [
    "CLAUDE.md",
    ".claude/settings.json",
    "harness/bin/watermark.py",
    "harness/bin/guard.py",
    "harness/bin/harness.py",
    "harness/bin/sync.py",
    "harness/hooks/post-write.sh",
    "harness/hooks/session-start.sh",
    "harness/hooks/user-prompt-submit.sh",
    "harness/hooks/stop.sh",
    "harness/protected.manifest",
]

STATE = HARNESS / ".state"
LAST_DAILY = STATE / "last-daily"


def _scope() -> list[str]:
    """Everything this operator is allowed to send: the shared corrections plus
    their own session log.

    Each path is checked for real FILES, not mere existence. Git cannot see an
    empty directory, and handing one to `git commit` as a pathspec fails the
    whole command ("pathspec did not match") — which leaves files staged, and a
    dirty index makes the pull refuse. The symptom is an operator who silently
    never syncs again, and it fires on a brand-new registration, because
    queries/<name>/ is empty until their first query.
    """
    paths = []
    for rel in (SCOPE, *_own_paths()):
        path = REPO / rel
        if path.is_dir() and any(c.is_file() for c in path.rglob("*")):
            paths.append(rel)
        elif path.is_file():
            paths.append(rel)
    return paths


def _own_paths() -> list[str]:
    """This operator's own chats/ and queries/ folders, if they are registered."""
    operator = HARNESS / ".operator"
    if not operator.exists():
        return []
    try:
        slug = json.loads(operator.read_text(encoding="utf-8")).get("slug", "")
    except Exception:
        return []
    return [f"chats/{slug}", f"queries/{slug}"] if slug else []

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

    # ff-only declined. If this machine simply has its own commits, that is the
    # normal state now (everyone writes a session note daily) and it must not be
    # treated as an error — replay ours on top instead.
    ahead = _git("rev-list", "--count", f"origin/{branch}..HEAD").stdout.strip()
    if ahead not in ("", "0"):
        r = _git("pull", "--rebase", "--autostash", "--quiet",
                 "origin", branch, timeout=max(NET_TIMEOUT, 60))
        if r.returncode == 0:
            n = _new_corrections_in(f"HEAD@{{1}}", "HEAD")
            msg = (f"jivo-sync: pulled {behind} update(s) and replayed your "
                   f"{ahead} on top")
            if n:
                msg += f" — {n} new correction(s) now active"
            print(msg)
            return 0
        # A rebase we cannot finish must never strand a non-technical operator
        # mid-conflict. Put the tree back exactly as it was and say so.
        for marker in ("rebase-merge", "rebase-apply"):
            if (REPO / ".git" / marker).exists():
                _git("rebase", "--abort", timeout=30)
                break
        print("jivo-sync: your work and the team's have changed the same thing, "
              "so this needs Daman to reconcile once. Nothing was changed and "
              "nothing is lost.", file=sys.stderr)
        return 0

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
    scope = _scope()
    if not scope:
        if not args.quiet:
            print("jivo-sync: nothing of yours to send yet")
        return 0
    st = _git("status", "--porcelain", "--", *scope)
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

    # Stage ONLY the corrections and this operator's own folders. This repo
    # routinely has dozens of unrelated modified files; a bare `git add -A` here
    # would ship somebody's WIP.
    if _git("add", "--", *scope).returncode != 0:
        print("jivo-sync: could not stage your work", file=sys.stderr)
        return 1

    staged = _git("diff", "--cached", "--name-only", "--", *scope).stdout.split()
    added = [f for f in staged if "/C-" in f and f.endswith(".md")]
    who = (os.environ.get("JIVO_USER") or os.environ.get("USER")
           or os.environ.get("USERNAME") or "operator")
    if len(added) == 1:
        subject = f"correction: {Path(added[0]).stem}"
    elif added:
        subject = f"corrections: {len(added)} update(s) from {who}"
    else:
        subject = f"logs({who}): {len(staged)} file(s) — {_dt.date.today().isoformat()}"
    body = ("Synced automatically by the harness on this operator's behalf.\n\n"
            "Files:\n" + "\n".join(f"  {f}" for f in staged))

    c = _git("commit", "-m", subject, "-m", body, "--", *scope)
    if c.returncode != 0:
        print(f"jivo-sync: commit failed — {(c.stderr or c.stdout).strip()[:200]}",
              file=sys.stderr)
        # Leave the index clean whatever happens: a staged-but-uncommitted file
        # blocks the next pull and strands this operator out of sync.
        _git("reset", "-q", "--", *scope)
        return 1

    note = (f"{len(added)} correction(s)" if added
            else f"{len(staged)} file(s) of your session log")
    return _do_push(branch, note=note)


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


# ── daily ────────────────────────────────────────────────────────────────────

def _ran_today() -> bool:
    try:
        return LAST_DAILY.read_text(encoding="utf-8").strip() == _dt.date.today().isoformat()
    except Exception:
        return False


def _restore_protected() -> list[str]:
    """Put back any protected file that was edited on this machine.

    This is the self-heal. An operator — or their agent, told to "tidy up the
    repo" — who edits CLAUDE.md or deletes a hook gets it restored, once a day,
    with nobody intervening. It touches ONLY the explicit list above: never a
    directory, never a glob, so it cannot reach the operator's real work.
    """
    restored = []
    for rel in PROTECTED:
        if not (REPO / rel).exists() and _git("cat-file", "-e", f"HEAD:{rel}").returncode != 0:
            continue                      # not in this checkout at all
        if not _git("status", "--porcelain", "--", rel).stdout.strip():
            continue                      # unchanged
        if _git("checkout", "--", rel).returncode == 0:
            restored.append(rel)
        else:
            print(f"jivo-sync: could not restore {rel} — this needs a human",
                  file=sys.stderr)
    return restored


def cmd_daily(args: argparse.Namespace) -> int:
    """The once-a-day cycle, called from the Stop hook.

    Deliberately hung off the Stop hook rather than cron: Windows has no cron,
    and asking a non-technical operator to set up Task Scheduler is asking for a
    fleet where half the machines never sync. The date check below costs nothing
    on the turns where it has already run.
    """
    if not (REPO / ".git").exists():
        return 0
    if _ran_today() and not args.force:
        return 0

    restored = _restore_protected()
    if restored:
        print(f"jivo-sync: restored {len(restored)} shared rule file(s) that had "
              f"been changed on this machine: {', '.join(restored)}",
              file=sys.stderr)

    # PULL UNCONDITIONALLY, and before the push. `push` returns early when this
    # operator has nothing to send, and the only pull inside the push path is in
    # _do_push — so relying on push to pull meant an operator who contributed
    # nothing that day received nothing either. Someone who only ever reads is
    # exactly the person who most needs other people's corrections.
    cmd_pull(argparse.Namespace(quiet=True))

    rc = cmd_push(argparse.Namespace(quiet=True))

    try:
        STATE.mkdir(parents=True, exist_ok=True)
        LAST_DAILY.write_text(_dt.date.today().isoformat() + "\n", encoding="utf-8")
    except Exception:
        pass                                        # a missed stamp only re-runs it

    guard = HARNESS / "bin" / "guard.py"
    if guard.exists():
        g = subprocess.run([sys.executable, str(guard), "check", "-q"],
                           cwd=REPO, capture_output=True, text=True, timeout=60)
        if g.returncode != 0:
            sys.stderr.write(g.stdout + g.stderr)
            return 1
    return rc


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
    scope = _scope()
    st = _git("status", "--porcelain", "--", *scope).stdout.splitlines() if scope else []
    print(f"  in scope        : {', '.join(scope) or '(nothing — not registered?)'}")
    print(f"  unsent locally  : {len([l for l in st if l.strip()])} change(s)")
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

    p = sub.add_parser("daily", help="once-a-day: repair the rules, pull, push")
    p.add_argument("-f", "--force", action="store_true",
                   help="run even if it already ran today")
    p.set_defaults(func=cmd_daily)

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
