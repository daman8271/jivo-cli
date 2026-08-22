"""Shared plumbing for summon grant scripts.

Every grant is a standalone executable that grantctl runs with a fixed set of
environment variables. This module holds the parts they all need, so a fix to the
Windows shell wrapping or the result shape lands in one place.

A grant NEVER decides policy — grantctl has already validated the grant name and
the box against policy.json and taken a per-box lock before this code runs.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys

ALIAS = os.environ.get("BOX_ALIAS") or os.environ.get("BOX_NAME") or ""
BOX = os.environ.get("BOX_NAME", ALIAS)
OS_KIND = (os.environ.get("BOX_OS") or "unknown").lower()
KIT = os.environ.get("BOX_KIT_PATH", "")
PROFILE = os.environ.get("BOX_PROFILE", "")
OPERATOR = os.environ.get("OPERATOR_SLUG", "")
OPERATOR_NAME = os.environ.get("OPERATOR_NAME", "") or OPERATOR
PERSONA = os.environ.get("OPERATOR_PERSONA") or ""
SAP_USER = os.environ.get("SAP_USER", "")
GRANT = os.environ.get("GRANT_NAME", "")
MODE = os.environ.get("GRANT_MODE", "check")
APPLY = MODE == "apply"
REASON = os.environ.get("GRANT_REASON", "")

WINDOWS = OS_KIND.startswith("win")

# The VPS reaches each box directly on 127.0.0.1:<tunnel_port> — it IS the tunnel
# endpoint, so unlike the Mac it needs no ProxyJump. install-vps.sh generates this
# file from policy.json. Root's own ~/.ssh/config is deliberately untouched: the
# fleet-health and auto-repair scripts depend on it.
SSH_CONFIG = os.environ.get(
    "SUMMON_SSH_CONFIG",
    os.path.join(os.environ.get("SUMMON_ROOT", "/opt/jivo-summon"), "ssh_config"))

# setup.py accepts only these; anything else fails argparse mid-grant.
DEPARTMENTS = {"accounts", "sales", "factory", "ecom", "exim", "ops", "hr", "it"}

# Facts about JIVO's fleet that were learned the hard way and that several grants
# need to check for.
DEAD_SAP_HOST = "103.89.45.192"      # decommissioned; the 502 everyone reports
READONLY_SAP_USERS = {"manager"}     # read-only at JIVO despite the name
DRAFT_SINCE = "6888265"              # first commit with `sapb1 draft`
RULE0_MARKER = "YOU MAY WRITE TO SAP"  # proves a box has commit a3b9465


class Report:
    """Accumulates what a grant found, did, and could not do."""

    def __init__(self, grant: str, box: str):
        self.grant = grant
        self.box = box
        self.findings: list[dict] = []
        self.actions: list[str] = []
        self.blockers: list[str] = []

    def note(self, step: str, ok: bool | None, detail: str) -> None:
        self.findings.append({"step": step, "ok": ok, "detail": detail})

    def did(self, what: str) -> None:
        self.actions.append(what)

    def blocked(self, why: str) -> None:
        self.blockers.append(why)

    def emit(self, message_ok: str = "", message_bad: str = "") -> "int":
        ok = not self.blockers
        print(json.dumps({
            "grant": self.grant,
            "box": self.box,
            "mode": MODE,
            "ok": ok,
            "findings": self.findings,
            "actions_taken": self.actions,
            "blockers": self.blockers,
            "operator_message": (
                (message_ok or f"{self.box}: {self.grant} is in place.") if ok
                else (message_bad or
                      f"{self.box} is not there yet — {len(self.blockers)} thing(s) "
                      f"in the way, listed above.")
            ),
        }, indent=2))
        return 0 if ok else 1


def ssh(inner: str, *, timeout: int = 90) -> tuple[int, str]:
    """Run a command on the box, wrapped for the box's real shell.

    Windows fleet boxes have PowerShell as the sshd default shell, and it rejects
    bash syntax (`||`, `2>/dev/null`) outright — so everything Windows-bound goes
    through `cmd /c`, chaining with `&`.
    """
    remote = f'cmd /c "{inner}"' if WINDOWS else inner
    try:
        cp = subprocess.run(
            ["ssh", "-F", SSH_CONFIG,
             "-o", "ConnectTimeout=12", "-o", "BatchMode=yes",
             "-o", "StrictHostKeyChecking=accept-new", ALIAS, remote],
            capture_output=True, text=True, timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s"
    return cp.returncode, (cp.stdout or "") + (cp.stderr or "")


def q(path: str) -> str:
    """Quote a path for the remote shell (cmd needs no quoting for our paths)."""
    return path if WINDOWS else shlex.quote(path)


def j(*parts: str) -> str:
    """Join path components with the box's separator."""
    sep = "\\" if WINDOWS else "/"
    return sep.join(p.rstrip("\\/") for p in parts if p)


def require_reachable(rep: Report) -> bool:
    """Confirm we have a shell. Returns False and records a blocker if not."""
    rc, out = ssh("hostname")
    if rc != 0:
        rep.note("reach", False, f"cannot ssh to {ALIAS}: {out.strip()[:240]}")
        rep.blocked(
            f"{BOX} is not reachable over the fleet tunnel right now, so nothing "
            f"can be provisioned on it. This grant is idempotent — it will simply "
            f"work on the operator's next 'Let's go' once the box is back up. "
            f"(A reverse tunnel that is refusing connections usually means the box "
            f"is off, asleep, or its sshd/tunnel service stopped.)"
        )
        return False
    host = out.strip().splitlines()[-1] if out.strip() else "?"
    rep.note("reach", True, f"reachable, hostname={host}")
    return True


def kit_is_git(rep: Report) -> bool | None:
    """Is the box's kit a real git checkout? None means we could not tell.

    The Drive-zip trap: an operator working from a month-old Google-Drive export
    (`jivo-cli-…Z-1-001`) has an old CLAUDE.md and a sapb1.exe with no `draft`, so
    no grant can help them. But the folder NAME alone does not prove it — one
    operator git-cloned *inside* the unzipped export, so the path looks like a zip
    while git works fine. Only a missing .git is disqualifying.
    """
    if not KIT:
        rep.blocked(
            f"policy.json has no kit_path for {BOX}. A human has to record where "
            f"this box's jivo-cli actually lives before anything can be granted — "
            f"on several Windows boxes it is NOT under the SSH login user's profile."
        )
        return None

    git_dir = j(KIT, ".git")
    probe = (f"if exist {git_dir} (echo GIT) else (echo NOGIT)" if WINDOWS
             else f"test -d {q(git_dir)} && echo GIT || echo NOGIT")
    rc, out = ssh(probe)
    if rc != 0:
        rep.note("checkout", None, f"could not probe {git_dir}: {out.strip()[:160]}")
        return None

    is_git = "GIT" in out and "NOGIT" not in out
    if not is_git:
        rep.note("checkout", False, f"{KIT} is not a git checkout")
        rep.blocked(
            f"{BOX} is working out of a folder that is not a git checkout ({KIT}) "
            f"— almost always an unzipped Google-Drive export. That is the single "
            f"most common reason an operator 'cannot write': the export's CLAUDE.md "
            f"still says read-only and its sapb1.exe predates the `draft` command "
            f"entirely, so no permission change reaches it. FIX: replace it with a "
            f"real `git clone`. That is a human step — I will not silently delete "
            f"somebody's folder."
        )
        return False

    rep.note("checkout", True, f"real git checkout at {KIT}")
    import re
    if re.search(r"Z-1-\d{3}", KIT):
        rep.note("checkout_path", True,
                 "path looks like a Drive export but IS a real checkout — pullable")
        rep.did(f"note: {BOX}'s kit sits inside an unzipped Drive export folder. It "
                f"syncs fine, but the path is confusing and worth tidying.")
    return True


def sync_kit(rep: Report) -> bool:
    """Fast-forward the box's kit, preserving any uncommitted work.

    NEVER reset --hard here. Operators have unpushed work in these checkouts — one
    box was carrying two dashboards nobody had pushed. A stash is recoverable; a
    hard reset is not.
    """
    # A stale 0-byte .git/index.lock silently blocks every git write. It stranded
    # one operator's commit for two days, twice.
    lock = j(KIT, ".git", "index.lock")
    if WINDOWS:
        rc, out = ssh(f"if exist {lock} (del /q {lock} & echo CLEARED)")
    else:
        rc, out = ssh(f"test -f {q(lock)} && rm -f {q(lock)} && echo CLEARED || true")
    if "CLEARED" in out:
        rep.note("index_lock", True, "cleared a stale .git/index.lock")
        rep.did(f"cleared a stale git index.lock on {BOX} that was blocking all git writes")

    rc, out = ssh(f"cd /d {KIT} & git fetch -q origin main" if WINDOWS
                  else f"cd {q(KIT)} && git fetch -q origin main", timeout=180)
    rep.note("fetch", rc == 0, out.strip()[-240:] or "fetched")
    if rc != 0:
        rep.blocked(f"{BOX} could not fetch from origin: {out.strip()[-200:]}")
        return False

    rc, dirty = ssh(f"cd /d {KIT} & git status --porcelain" if WINDOWS
                    else f"cd {q(KIT)} && git status --porcelain")
    if dirty.strip():
        # Untracked-only is safe to leave: a fast-forward cannot clobber files git
        # is not tracking, and stashing them would hide the operator's own work.
        lines = [l for l in dirty.splitlines() if l.strip()]
        tracked = [l for l in lines if not l.startswith("??")]
        if tracked:
            rc, out = ssh(f'cd /d {KIT} & git stash push -u -m "pre-summon"' if WINDOWS
                          else f'cd {q(KIT)} && git stash push -u -m "pre-summon"',
                          timeout=120)
            rep.note("stash", rc == 0, out.strip()[-200:])
            rep.did(f"STASHED uncommitted work on {BOX} before syncing. The operator "
                    f"gets it back with `git stash pop` — tell them, they do not know.")
        else:
            rep.note("dirty", True,
                     f"{len(lines)} untracked path(s) left alone — a ff-merge cannot "
                     f"touch untracked files, and stashing would hide their work")

    rc, out = ssh(f"cd /d {KIT} & git merge --ff-only origin/main" if WINDOWS
                  else f"cd {q(KIT)} && git merge --ff-only origin/main", timeout=120)
    if rc != 0:
        rep.note("ff_merge", False, out.strip()[-240:])
        rep.blocked(
            f"{BOX}'s checkout has diverged from origin/main and will not "
            f"fast-forward. Not forcing it — a checkout with local commits is a "
            f"human's call, and forcing it would throw away whatever they did."
        )
        return False

    rc, head = ssh(f"cd /d {KIT} & git rev-parse --short HEAD" if WINDOWS
                   else f"cd {q(KIT)} && git rev-parse --short HEAD")
    rep.note("ff_merge", True, f"now at {head.strip()[:12]}")
    rep.did(f"synced {BOX} to origin/main ({head.strip()[:12]})")
    return True


def verify_rule0(rep: Report) -> bool:
    """Read back the box's own CLAUDE.md. A clean `git pull` is not evidence."""
    cm = j(KIT, "CLAUDE.md")
    grep = (f'findstr /c:"{RULE0_MARKER}" {cm}' if WINDOWS
            else f'grep -F "{RULE0_MARKER}" {q(cm)}')
    rc, out = ssh(grep)
    if RULE0_MARKER in out:
        rep.note("rule0", True, "repo RULE 0 allows SAP writes on this box")
        return True
    rep.note("rule0", False, "box's CLAUDE.md predates commit a3b9465")
    rep.blocked(
        f"{BOX} has not picked up the RULE 0 commit (a3b9465) yet, so the Claude "
        f"running there will still refuse to write to SAP. This is a sync problem, "
        f"not a permission problem."
    )
    return False
