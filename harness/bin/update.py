#!/usr/bin/env python3
"""JIVO update — the daily catch-up, and the thing that repairs the rules.

Runs once a day on every operator's machine, unattended. Four jobs, in order:

  1. Commit this operator's session log (`chats/<slug>/`, `queries/<slug>/`)
     and anything they added to the shared stores (`harness/corrections/`,
     `harness/questions/`) — corrections have to reach everyone or the
     single shared brain is a fiction.
  2. Restore the protected files, discarding any local edit to them.
  3. Pull `main` and push, so one shared history converges.
  4. Re-check the integrity seal and report.

This tool NEVER touches SAP or any business system. It runs git, and only git.

Safety rules it will not break
------------------------------
It runs on the laptop of someone who cannot fix git, so it is written to fail
safe rather than to succeed cleverly:

  * NEVER `git reset --hard`, NEVER `git clean`. Both would destroy work the
    operator has not pushed. A stale checkout is recoverable; deleted work is
    not.
  * `git checkout --` is issued ONLY against the explicit protected-path list.
    It is never given a directory, a glob, or `.`.
  * It stages only this operator's own folders plus the two shared stores.
    Another operator's logs, and any half-finished work elsewhere in the
    tree, are left alone — and `--autostash` means a dirty tree delays
    nothing and loses nothing.
  * On a conflict it aborts, leaves the tree as git left it, and says so in
    plain language. It never forces, never rebases blindly, never pushes over
    anyone.
  * No network, no remote, not a git repo, nothing to do: exit 0 quietly and
    try again tomorrow.

Subcommands
-----------
  run       Do the daily cycle (skips if it already ran today).
  status    What it would do, without doing it.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent
REPO = HARNESS.parent
OPERATOR = HARNESS / ".operator"
STATE = HARNESS / ".state"
LAST_RUN = STATE / "last-update"

# Exactly the files guard.py seals. Restoring anything beyond this list risks
# throwing away an operator's real work, so the list is explicit and closed.
PROTECTED = [
    "CLAUDE.md",
    ".claude/settings.json",
    "harness/bin/watermark.py",
    "harness/bin/guard.py",
    "harness/bin/harness.py",
    "harness/bin/update.py",
    "harness/hooks/post-write.sh",
    "harness/hooks/session-start.sh",
    "harness/hooks/user-prompt-submit.sh",
    "harness/hooks/stop.sh",
    "harness/protected.manifest",
]

TIMEOUT = 120


def _git(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True,
        timeout=TIMEOUT, check=check,
    )


def _ok(*args: str) -> bool:
    try:
        return _git(*args).returncode == 0
    except Exception:
        return False


def _operator() -> dict | None:
    if not OPERATOR.exists():
        return None
    try:
        return json.loads(OPERATOR.read_text(encoding="utf-8"))
    except Exception:
        return None


def _ran_today() -> bool:
    if not LAST_RUN.exists():
        return False
    try:
        return LAST_RUN.read_text(encoding="utf-8").strip() == _dt.date.today().isoformat()
    except Exception:
        return False


def _mark_ran() -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    LAST_RUN.write_text(_dt.date.today().isoformat() + "\n", encoding="utf-8")


def _log(msg: str) -> None:
    print(f"update: {msg}")


# ── the four steps ──────────────────────────────────────────────────────────

def _commit_own_logs(slug: str) -> bool:
    """Stage and commit ONLY this operator's own folders. Returns True if it
    created a commit.

    Every path is checked for actual FILES first, not just existence. Git cannot
    see an empty directory, so passing one as a pathspec makes the whole `git
    commit` fail with "pathspec did not match" — which used to leave files
    staged but uncommitted, and a dirty index makes the subsequent
    `pull --rebase` refuse to run. The visible symptom was an operator who
    silently never synced, every day, forever. `setup.py` creates
    `queries/<slug>/` empty, so this hit every new operator on day one.
    """
    # This operator's own session log, PLUS the two shared stores they are
    # allowed to add to. Corrections are the whole point of the single shared
    # brain: an operator catches Claude getting a JIVO metric wrong, records it,
    # and it has to reach everyone. Left out of this list, a correction is
    # written to their laptop and never leaves it — the loop looks like it works
    # and silently doesn't. `harness/corrections/INDEX.md` and
    # `harness/questions/log.jsonl` are merge=union in .gitattributes, so
    # several operators appending on the same day merge without a human.
    candidates = [
        f"chats/{slug}",
        f"queries/{slug}",
        "harness/corrections",
        "harness/questions",
    ]
    mine = []
    for rel in candidates:
        path = REPO / rel
        if path.is_dir() and any(p.is_file() for p in path.rglob("*")):
            mine.append(rel)
        elif path.is_file():
            mine.append(rel)
    if not mine:
        return False

    _git("add", "--", *mine)
    staged = _git("diff", "--cached", "--name-only", "--", *mine).stdout.strip()
    if not staged:
        return False

    n = len(staged.splitlines())
    msg = f"logs({slug}): {n} file(s) — {_dt.date.today().isoformat()}"
    if any(m.startswith("harness/corrections") for m in mine) and \
            any("corrections/C-" in line for line in staged.splitlines()):
        msg = f"correction+logs({slug}) — {_dt.date.today().isoformat()}"
    result = _git("commit", "-m", msg, "--", *mine)
    if result.returncode != 0:
        _log(f"could not commit own logs: {result.stderr.strip()[:160]}")
        # Leave the index clean whatever happens. A staged-but-uncommitted file
        # would block the pull below and strand this operator out of sync.
        _git("reset", "-q", "--", *mine)
        return False
    _log(f"committed {n} file(s) of your own log")
    return True


def _restore_protected() -> list[str]:
    """Discard local edits to the protected files. Returns what was restored.

    This is the self-heal. An operator (or their agent) who edits CLAUDE.md or
    deletes a hook gets it put back, once a day, without anyone intervening.
    """
    restored = []
    for rel in PROTECTED:
        if not (REPO / rel).exists() and not _ok("cat-file", "-e", f"HEAD:{rel}"):
            continue  # not in this checkout at all; nothing to restore to
        dirty = _git("status", "--porcelain", "--", rel).stdout.strip()
        if not dirty:
            continue
        if _git("checkout", "--", rel).returncode == 0:
            restored.append(rel)
            _log(f"restored {rel} (local edit discarded)")
        else:
            _log(f"COULD NOT restore {rel} — needs a human")
    return restored


def _sync() -> str:
    """Pull then push. Returns one of: ok, no-remote, offline, conflict, push-failed."""
    if not _git("remote").stdout.strip():
        return "no-remote"

    if _git("fetch", "--quiet", "origin").returncode != 0:
        return "offline"

    branch = _git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip() or "main"

    # --rebase so this operator's log commit replays on top of everyone else's
    # instead of producing a merge commit per person per day. chats/**/*.md and
    # queries/**/*.jsonl are merge=union in .gitattributes, so the common case
    # (several people appending the same day) resolves without a human.
    #
    # --autostash is not optional. Plain `pull --rebase` REFUSES outright if the
    # tree has any unstaged change at all — "cannot pull with rebase: You have
    # unstaged changes" — and it does not care whether the change is in a file we
    # touch. A non-technical operator always has some stray modified file, so
    # without this the daily sync fails, gets reported as a conflict, and that
    # laptop silently stops syncing forever. --autostash stashes, rebases and
    # restores; if the restore conflicts, git leaves the work in the stash rather
    # than dropping it.
    pull = _git("pull", "--rebase", "--autostash", "--quiet", "origin", branch)
    if pull.returncode != 0:
        # Leave the tree exactly as git left it, but do not strand a
        # non-technical operator mid-rebase.
        if (REPO / ".git" / "rebase-merge").exists() or (REPO / ".git" / "rebase-apply").exists():
            _git("rebase", "--abort")
            _log("pull conflicted — aborted cleanly, nothing was lost")
        return "conflict"

    push = _git("push", "--quiet", "origin", branch)
    if push.returncode != 0:
        # Someone pushed between our fetch and our push. One retry, then leave
        # it for tomorrow rather than looping or forcing.
        _git("pull", "--rebase", "--autostash", "--quiet", "origin", branch)
        if _git("push", "--quiet", "origin", branch).returncode != 0:
            return "push-failed"
    return "ok"


def _guard_check() -> int:
    guard = HARNESS / "bin" / "guard.py"
    if not guard.exists():
        return 0
    result = subprocess.run(
        [sys.executable, str(guard), "check", "-q"],
        cwd=REPO, capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout + result.stderr)
    return result.returncode


# ── commands ────────────────────────────────────────────────────────────────

def cmd_run(args: argparse.Namespace) -> int:
    if not (REPO / ".git").exists():
        return 0
    if _ran_today() and not args.force:
        if args.verbose:
            _log("already ran today")
        return 0

    reg = _operator()
    slug = (reg or {}).get("slug", "")

    if slug:
        _commit_own_logs(slug)
    elif args.verbose:
        _log("not registered — run harness/bin/setup.py (skipping log commit)")

    restored = _restore_protected()

    outcome = _sync()
    {
        "ok": lambda: _log("synced with main"),
        "no-remote": lambda: _log("no remote configured — nothing to sync"),
        "offline": lambda: _log("offline — will try again tomorrow"),
        "conflict": lambda: _log("could not merge automatically — tell Daman"),
        "push-failed": lambda: _log("could not push — will try again tomorrow"),
    }[outcome]()

    # Only claim the day when we actually reached the remote. An offline laptop
    # should retry on the next session, not go quiet for 24 hours.
    if outcome in ("ok", "no-remote"):
        _mark_ran()

    rc = _guard_check()
    if restored:
        _log(f"self-healed {len(restored)} protected file(s)")
    return 0 if rc == 0 else 1


def cmd_status(args: argparse.Namespace) -> int:
    reg = _operator()
    print(f"operator   : {reg.get('name') if reg else '(not registered)'}")
    print(f"slug       : {reg.get('slug') if reg else '-'}")
    print(f"ran today  : {'yes' if _ran_today() else 'no'}")
    print(f"branch     : {_git('rev-parse', '--abbrev-ref', 'HEAD').stdout.strip() or '?'}")
    print(f"remote     : {_git('remote').stdout.strip() or '(none)'}")
    dirty = [rel for rel in PROTECTED
             if _git("status", "--porcelain", "--", rel).stdout.strip()]
    print(f"protected  : {len(dirty)} locally modified"
          + (f" → {', '.join(dirty)}" if dirty else ""))
    if reg and reg.get("slug"):
        slug = reg["slug"]
        pending = _git("status", "--porcelain", "--",
                       f"chats/{slug}", f"queries/{slug}").stdout.strip()
        print(f"your logs  : {len(pending.splitlines()) if pending else 0} uncommitted file(s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="update", description="Daily catch-up and rule self-heal.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run", help="do the daily cycle")
    p.add_argument("-f", "--force", action="store_true", help="run even if it already ran today")
    p.add_argument("-v", "--verbose", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("status", help="show what it would do")
    p.set_defaults(func=cmd_status)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
