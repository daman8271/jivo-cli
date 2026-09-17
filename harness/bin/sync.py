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
  * An update this tool started and that never finished is cleaned up on the
    next run (2026-09-17). Measured that day: 8 of 12 Accounts checkouts were
    frozen — weeks behind, running old guards — by a `.git/index.lock`, a
    `.git/rebase-merge` or a detached HEAD left by a git that was killed half
    way (the merge had a 30-second timeout; a commit with three 16 MB binaries
    takes longer on an office PC). Anything older than STALE_SECONDS is
    leftover, not a live operation: its autostash is kept as a stash entry and
    the branch is put back where it was.
  * Two kinds of tracked file never block an update: the rules digest (rebuilt
    right after every pull) and per-machine files (this operator's own SAP
    login and registration), whose bytes are put back after the update.
  * FOLLOW-MAIN boxes (`git config jivo.followMain true`, set on office
    operator PCs, which cannot push anyway) never stay behind. When the normal
    update is refused, local commits are kept on a `backup/kept-<time>` branch,
    local edits to files the team changed are copied to `.git/jivo-kept/<time>/`,
    the branch is moved to the team's, and this operator's own session log and
    corrections are written back. Off by default: the owner's Mac keeps the
    old, cautious behaviour.
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
import shutil
import subprocess
import sys
import time
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

# Local git work (merge, rebase, checkout) is bounded generously. Killing git in
# the middle of writing the working tree is what left the index.lock behind.
LOCAL_TIMEOUT = 900

# A lock or rebase folder older than this was left by a git that died.
STALE_SECONDS = 600

# Rebuilt from harness/corrections/ right after every pull, so a local copy of
# it is never worth keeping and must never block an update.
GENERATED = ["harness/corrections/INDEX.md"]

# This machine's own identity. Tracked for historical reasons; the local bytes
# are what make this operator's writes go out under THEIR SAP login, so they are
# put back after any update that touches them.
MACHINE_FILES = [
    "sap-b1/accounts-kit/.env",
    "sap-b1/accounts-kit/use.cmd",
    "sap-b1/cli/.env",
    "sap-b1/cli/use.cmd",
    "harness/.operator",
    "harness/.persona",
]


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

def _git_dir() -> Path:
    r = _git("rev-parse", "--git-dir")
    d = Path((r.stdout or ".git").strip())
    return d if d.is_absolute() else REPO / d


def _age(path: Path) -> float:
    try:
        return time.time() - path.stat().st_mtime
    except OSError:
        return 0.0


def _heal() -> list[str]:
    """Clean up after an update that died half way. Returns what was done."""
    gd, done = _git_dir(), []

    lock = gd / "index.lock"
    if lock.exists() and _age(lock) > STALE_SECONDS:
        try:
            lock.unlink()
            done.append("removed a stale index.lock")
        except OSError:
            pass

    for marker in ("rebase-merge", "rebase-apply"):
        d = gd / marker
        if not d.exists() or _age(d) <= STALE_SECONDS:
            continue
        stash = d / "autostash"
        if stash.exists():
            sha = stash.read_text(encoding="utf-8", errors="replace").strip()
            if sha:
                _git("stash", "store", "-m",
                     "local edits held by an unfinished update (kept by jivo-sync)", sha)
                done.append("kept the unfinished update's local edits as a stash entry")
        head_name = (d / "head-name").read_text(encoding="utf-8").strip() if (d / "head-name").exists() else ""
        orig_head = (d / "orig-head").read_text(encoding="utf-8").strip() if (d / "orig-head").exists() else ""
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        _git("branch", "-f", f"backup/unfinished-update-{stamp}", "HEAD")
        _git("rebase", "--quit", timeout=LOCAL_TIMEOUT)
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
        branch = head_name[len("refs/heads/"):] if head_name.startswith("refs/heads/") else ""
        if branch and orig_head:
            # Back to exactly where the branch was before the update started.
            # What the half-done rebase had written is on the backup branch.
            _git("checkout", "-f", "-B", branch, orig_head, timeout=LOCAL_TIMEOUT)
        done.append(f"cleared an unfinished update ({marker})")

    merge_head = gd / "MERGE_HEAD"
    if merge_head.exists() and _age(merge_head) > STALE_SECONDS:
        _git("merge", "--abort", timeout=LOCAL_TIMEOUT)
        done.append("cleared an unfinished merge")
    return done


def _dirty_tracked() -> set[str]:
    r = _git("-c", "core.quotepath=off", "status", "--porcelain", "--untracked-files=no")
    out = set()
    for ln in r.stdout.splitlines():
        if len(ln) > 3:
            path = ln[3:].split(" -> ")[-1].strip().strip('"')
            out.add(path)
    return out


def _follow_main() -> bool:
    return _git("config", "--get", "jivo.followMain").stdout.strip().lower() == "true"


def _background_fetch(branch: str) -> None:
    """A slow line cannot bring a big update down inside a session-start
    timeout, and a timed-out fetch starts from zero next time. Let it finish on
    its own so the next session has the objects."""
    cmd = ["git", "-C", str(REPO), "fetch", "--quiet", "origin", branch]
    try:
        if os.name == "nt":
            flags = 0x00000008 | 0x00000200 | 0x08000000  # DETACHED | NEW_GROUP | NO_WINDOW
            subprocess.Popen(cmd, creationflags=flags, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(cmd, start_new_session=True, stdin=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def cmd_pull(args: argparse.Namespace) -> int:
    ok, why = _usable_repo()
    if not ok:
        if args.quiet:
            return 0
        print(f"jivo-sync: {why}", file=sys.stderr)
        return 0

    healed = _heal()
    if healed:
        print("jivo-sync: " + "; ".join(healed), file=sys.stderr)

    branch = _branch()
    if not branch or branch == "HEAD":
        if not args.quiet:
            print("jivo-sync: detached HEAD — not pulling", file=sys.stderr)
        return 0

    try:
        f = _git("fetch", "--quiet", "origin", branch, timeout=NET_TIMEOUT)
    except subprocess.TimeoutExpired:
        _background_fetch(branch)
        if not args.quiet:
            print(f"jivo-sync: remote unreachable within {NET_TIMEOUT}s — "
                  "using the corrections already on this machine (still "
                  "downloading in the background for next time)", file=sys.stderr)
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

    # Files the team changed that are also changed here. The digest is rebuilt
    # after the pull, and per-machine files get their bytes back afterwards, so
    # neither is allowed to stop the update.
    incoming = set(_git("diff", "--name-only", "HEAD", f"origin/{branch}").stdout.split())
    kept: dict[str, bytes | None] = {}
    for rel in sorted(incoming & _dirty_tracked()):
        if rel in MACHINE_FILES:
            path = REPO / rel
            kept[rel] = path.read_bytes() if path.exists() else None
            _git("checkout", "--", rel)
        elif rel in GENERATED:
            _git("checkout", "--", rel)
    try:
        return _pull_update(args, branch, behind, incoming)
    finally:
        for rel, data in kept.items():
            path = REPO / rel
            try:
                if data is None:
                    if path.exists():
                        path.unlink()
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
            except OSError as e:
                print(f"jivo-sync: could not put back this machine's {rel}: {e}",
                      file=sys.stderr)


def _pull_update(args: argparse.Namespace, branch: str, behind: str, incoming: set[str]) -> int:
    # A fast-forward is the only merge that cannot conflict or lose a commit.
    m = _git("merge", "--ff-only", f"origin/{branch}", timeout=LOCAL_TIMEOUT)
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
        r = _git("rebase", "--autostash", f"origin/{branch}", timeout=LOCAL_TIMEOUT)
        if r.returncode == 0:
            n = _new_corrections_in(f"HEAD@{{1}}", "HEAD")
            msg = (f"jivo-sync: pulled {behind} update(s) and replayed your "
                   f"{ahead} on top")
            if n:
                msg += f" — {n} new correction(s) now active"
            print(msg)
            return 0
        # A rebase we cannot finish must never strand a non-technical operator
        # mid-conflict. Put the tree back exactly as it was.
        for marker in ("rebase-merge", "rebase-apply"):
            if (_git_dir() / marker).exists():
                _git("rebase", "--abort", timeout=LOCAL_TIMEOUT)
                break

    if _follow_main():
        return _follow_team(branch, behind, ahead not in ("", "0"), incoming)

    if ahead not in ("", "0"):
        print("jivo-sync: your work and the team's have changed the same thing, "
              "so this needs Daman to reconcile once. Nothing was changed and "
              "nothing is lost.", file=sys.stderr)
        return 0
    print("jivo-sync: cannot auto-update — local edits would be overwritten. "
          f"Nothing was changed. {(m.stderr or '').strip().splitlines()[:1]}",
          file=sys.stderr)
    return 0


def _follow_team(branch: str, behind: str, has_local_commits: bool, incoming: set[str]) -> int:
    """An office box that cannot push must never stay behind the team: behind
    means old guards and old skills, doing real entries. Keep everything, then
    move to the team's version."""
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    kept_dir = _git_dir() / "jivo-kept" / stamp
    backup = f"backup/kept-{stamp}"
    if has_local_commits:
        _git("branch", "-f", backup, "HEAD")

    clashing = sorted(incoming & _dirty_tracked())
    for rel in clashing:
        src = REPO / rel
        if src.exists():
            dst = kept_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    if clashing:
        _git("checkout", "--", *clashing)

    c = _git("checkout", "-B", branch, f"origin/{branch}", timeout=LOCAL_TIMEOUT)
    if c.returncode != 0:
        print("jivo-sync: could not bring this machine up to date — "
              f"{(c.stderr or '').strip().splitlines()[:1]}. Nothing was lost"
              + (f"; local commits are on {backup}" if has_local_commits else "")
              + (f"; local edits copied to {kept_dir}" if clashing else ""),
              file=sys.stderr)
        return 0

    # This operator's own session log and their corrections live only here
    # (the box cannot push). Write them back so nothing they recorded vanishes
    # from the working tree; they stay out of the branch until Daman takes them.
    restored = 0
    if has_local_commits:
        own = [*_own_paths(), SCOPE]
        changed = _git("diff", "--name-only", "--diff-filter=AM",
                       f"origin/{branch}", backup, "--", *own).stdout.split()
        for rel in changed:
            if rel in GENERATED:
                continue
            blob = subprocess.run(["git", "-C", str(REPO), "show", f"{backup}:{rel}"],
                                  capture_output=True, timeout=60)
            if blob.returncode == 0:
                path = REPO / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(blob.stdout)
                restored += 1

    kept = []
    if has_local_commits:
        kept.append(f"your commits on {backup}")
    if clashing:
        kept.append(f"{len(clashing)} locally edited file(s) in {kept_dir}")
    if restored:
        kept.append(f"{restored} of your own log/correction file(s) written back")
    print(f"jivo-sync: brought this machine level with the team ({behind} update(s))"
          + (" — kept " + "; ".join(kept) if kept else ""))
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
        print("jivo-sync: git timed out — the next run cleans up anything it "
              "left half done", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
