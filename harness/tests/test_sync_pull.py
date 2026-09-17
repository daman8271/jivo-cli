"""sync pull: a box must not freeze behind the team (2026-09-17).

That day 8 of 12 Accounts checkouts were weeks behind main, running old guards,
frozen by what a killed git left behind or by a local edit to a file the team
changed. Each test builds a real origin + operator clone and recreates one of
those states, then runs the real sync.py inside the clone.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

SYNC = Path(__file__).resolve().parent.parent / "bin" / "sync.py"


def git(cwd, *args, check=True):
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {r.stderr}")
    return r.stdout.strip()


def write(root, rel, text):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def commit_all(cwd, msg):
    git(cwd, "add", "-A")
    git(cwd, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", msg)


@pytest.fixture
def team(tmp_path):
    """origin (bare), the team's working copy that pushes, and an operator box."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    daman = tmp_path / "daman"
    subprocess.run(["git", "clone", "-q", str(origin), str(daman)], check=True)
    git(daman, "checkout", "-q", "-b", "main")
    write(daman, "harness/bin/sync.py", SYNC.read_text(encoding="utf-8"))
    write(daman, "harness/corrections/INDEX.md", "rules v1\n")
    write(daman, "harness/corrections/C-0001-a.md", "rule a\n")
    write(daman, ".claude/skills/x/SKILL.md", "skill v1\n")
    write(daman, "sap-b1/cli/.env", "SAPB1_USER=manager\n")
    write(daman, "harness/.operator", '{"slug": "user05"}\n')
    commit_all(daman, "base")
    git(daman, "push", "-q", "origin", "main")
    box = tmp_path / "box"
    subprocess.run(["git", "clone", "-q", str(origin), str(box)], check=True)
    return daman, box


def team_update(daman, rel, text, msg="team update"):
    write(daman, rel, text)
    commit_all(daman, msg)
    git(daman, "push", "-q", "origin", "main")


def pull(box):
    r = subprocess.run([sys.executable, str(Path(box) / "harness/bin/sync.py"), "pull"],
                       capture_output=True, text=True, cwd=box, timeout=120)
    return r.stdout + r.stderr


def up_to_date(box):
    git(box, "fetch", "-q", "origin")
    return git(box, "rev-parse", "HEAD") == git(box, "rev-parse", "origin/main")


def make_old(path):
    old = time.time() - 3600
    os.utime(path, (old, old))


def test_a_stale_index_lock_no_longer_freezes_the_box(team):
    daman, box = team
    team_update(daman, ".claude/skills/x/SKILL.md", "skill v2\n")
    lock = box / ".git" / "index.lock"
    lock.write_text("")
    make_old(lock)

    out = pull(box)
    assert "stale index.lock" in out
    assert up_to_date(box)
    assert (box / ".claude/skills/x/SKILL.md").read_text() == "skill v2\n"


def test_a_fresh_lock_is_left_alone(team):
    daman, box = team
    team_update(daman, ".claude/skills/x/SKILL.md", "skill v2\n")
    lock = box / ".git" / "index.lock"
    lock.write_text("")

    pull(box)
    assert lock.exists(), "a lock younger than STALE_SECONDS may belong to a live git"


def test_an_unfinished_rebase_is_cleared_and_its_autostash_kept(team):
    daman, box = team
    # A local commit and an uncommitted edit, then a rebase that stops on a conflict.
    write(box, ".claude/skills/x/SKILL.md", "operator's skill\n")
    commit_all(box, "operator commit")
    write(box, "notes.txt", "tracked note\n")
    commit_all(box, "note")
    write(box, "notes.txt", "uncommitted operator edit\n")
    team_update(daman, ".claude/skills/x/SKILL.md", "skill v2\n")
    git(box, "fetch", "-q", "origin")
    git(box, "-c", "user.email=t@t", "-c", "user.name=t", "rebase", "--autostash", "origin/main", check=False)
    rebase_dir = box / ".git" / "rebase-merge"
    assert rebase_dir.exists(), "test setup: the rebase should have stopped on the conflict"
    for p in [rebase_dir, *rebase_dir.rglob("*")]:
        make_old(p)

    out = pull(box)
    assert "cleared an unfinished update" in out
    assert not rebase_dir.exists()
    assert git(box, "rev-parse", "--abbrev-ref", "HEAD") == "main", "must not be left on a detached HEAD"
    assert "local edits held by an unfinished update" in git(box, "stash", "list")
    assert any(b.strip().startswith("backup/unfinished-update-") for b in git(box, "branch", "--list", "backup/*").splitlines())


def test_the_rules_digest_never_blocks_an_update(team):
    daman, box = team
    write(box, "harness/corrections/INDEX.md", "rebuilt locally with a persona filter\n")
    team_update(daman, "harness/corrections/INDEX.md", "rules v2\n")

    pull(box)
    assert up_to_date(box)


def test_this_machines_login_survives_an_update_that_touches_it(team):
    daman, box = team
    write(box, "sap-b1/cli/.env", "SAPB1_USER=USER19\n")
    write(box, "harness/.operator", '{"slug": "mahak"}\n')
    team_update(daman, "sap-b1/cli/.env", "SAPB1_USER=manager\nSAPB1_TIMEOUT=60\n")
    team_update(daman, "harness/.operator", '{"slug": "user05", "x": 1}\n')

    pull(box)
    assert up_to_date(box)
    assert (box / "sap-b1/cli/.env").read_text() == "SAPB1_USER=USER19\n"
    assert (box / "harness/.operator").read_text() == '{"slug": "mahak"}\n'


def test_the_login_is_put_back_even_when_the_update_is_refused(team):
    daman, box = team
    write(box, "sap-b1/cli/.env", "SAPB1_USER=USER19\n")
    write(box, ".claude/skills/x/SKILL.md", "operator's local skill edit\n")
    team_update(daman, "sap-b1/cli/.env", "SAPB1_USER=manager\nSAPB1_TIMEOUT=60\n")
    team_update(daman, ".claude/skills/x/SKILL.md", "skill v2\n")

    out = pull(box)  # jivo.followMain not set: the old, cautious behaviour
    assert "cannot auto-update" in out
    assert not up_to_date(box)
    assert (box / "sap-b1/cli/.env").read_text() == "SAPB1_USER=USER19\n"
    assert (box / ".claude/skills/x/SKILL.md").read_text() == "operator's local skill edit\n"


def test_follow_main_box_keeps_the_local_edit_and_takes_the_team_version(team):
    daman, box = team
    git(box, "config", "jivo.followMain", "true")
    write(box, ".claude/skills/x/SKILL.md", "operator's local skill edit\n")
    team_update(daman, ".claude/skills/x/SKILL.md", "skill v2\n")

    out = pull(box)
    assert up_to_date(box)
    assert (box / ".claude/skills/x/SKILL.md").read_text() == "skill v2\n"
    kept = list((box / ".git" / "jivo-kept").rglob("SKILL.md"))
    assert kept and kept[0].read_text() == "operator's local skill edit\n", out


def test_follow_main_box_with_diverged_commits_keeps_them_and_its_own_log(team):
    daman, box = team
    git(box, "config", "jivo.followMain", "true")
    write(box, "harness/.operator", '{"slug": "mahak"}\n')
    git(box, "update-index", "--skip-worktree", "harness/.operator")
    write(box, "queries/mahak/sap-writes.jsonl", '{"line": 1}\n')
    write(box, "harness/corrections/C-0090-local-rule.md", "mahak's rule\n")
    write(box, ".claude/skills/x/SKILL.md", "operator's committed skill edit\n")
    commit_all(box, "local work the box cannot push")
    team_update(daman, ".claude/skills/x/SKILL.md", "skill v2\n")
    team_update(daman, "harness/corrections/C-0090-team-rule.md", "team rule\n")

    out = pull(box)
    assert up_to_date(box), out
    assert (box / ".claude/skills/x/SKILL.md").read_text() == "skill v2\n"
    assert (box / "queries/mahak/sap-writes.jsonl").read_text() == '{"line": 1}\n'
    assert (box / "harness/corrections/C-0090-local-rule.md").read_text() == "mahak's rule\n"
    assert any("backup/kept-" in b for b in git(box, "branch", "--list", "backup/*").splitlines())


def test_the_next_update_after_follow_main_is_a_plain_one(team):
    daman, box = team
    git(box, "config", "jivo.followMain", "true")
    write(box, ".claude/skills/x/SKILL.md", "operator's local skill edit\n")
    team_update(daman, ".claude/skills/x/SKILL.md", "skill v2\n")
    pull(box)
    team_update(daman, ".claude/skills/x/SKILL.md", "skill v3\n")

    out = pull(box)
    assert "pulled 1 update(s) from the team" in out
    assert up_to_date(box)
