"""Read-only git time-travel over an ecom-intel checkout.

The ecom-intel repo commits EVERY sweep (subjects like ``run: flipkart
2026-07-19-1008``), so files that later get overwritten -- notably
``platforms/<p>/result.json`` -- stay recoverable for any past date through
read-only git plumbing. This module is the ONLY place in the CLI that shells
out, and it does so under a hard contract:

* subprocess with an explicit argv LIST and ``shell=False`` (never a string,
  never a shell) so nothing can be injected through a path or a subject;
* the ONLY git verbs it may ever build are ``rev-list``, ``show``, ``log``,
  ``rev-parse`` and ``ls-tree`` -- all read-only. Building any other verb is
  refused with a ValueError. There is no add/commit/checkout/reset/clean/fetch/gc
  path here;
* it never opens a data file for writing and never touches the network.

READ-ONLY LAW: git history is a source we *read*; we never mutate the repo.

When ``root`` is not a git checkout (or the ``git`` binary is missing), the
recover helpers raise :class:`FileNotFoundError` so the dispatcher can print a
clean "source missing" line and exit 3 -- never a traceback.
"""

import datetime as _dt
import os
import subprocess

# The complete allow-list of git subcommands this module may invoke. Every one
# is read-only. Keep this frozen: a new verb here must be provably read-only.
_READ_ONLY_VERBS = frozenset({"rev-list", "show", "log", "rev-parse", "ls-tree"})

# ASCII unit separator -- safe field delimiter for --pretty output, since it
# cannot occur inside a commit subject line.
_US = "\x1f"


def _git(root, *argv):
    """Run one read-only git verb under ``root`` and return the CompletedProcess.

    stdout/stderr are captured as raw bytes (``show`` must return file bytes
    verbatim). ``check=False`` -- callers inspect ``returncode`` themselves so a
    "path absent at this commit" is data, not an exception.

    Raises:
        ValueError: if ``argv`` does not start with an allow-listed read-only
            verb (defensive -- indicates a programming error in this module).
        FileNotFoundError: if the ``git`` binary cannot be executed.
    """
    if not argv or argv[0] not in _READ_ONLY_VERBS:
        raise ValueError(
            "gittime: refusing non-read-only git verb: %r" % (argv[:1] or [None])[0]
        )
    cmd = ["git", "-C", str(root), *[str(a) for a in argv]]
    try:
        return subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            check=False,
        )
    except FileNotFoundError:
        # git itself is not installed / not on PATH.
        raise FileNotFoundError("gittime: git binary not found on PATH")


def _out(cp):
    """Decode a CompletedProcess's stdout to text (lenient)."""
    return cp.stdout.decode("utf-8", "replace")


def is_git_root(root):
    """True when ``root`` is the top of a git work tree.

    A pure, non-raising probe: returns False for a plain directory, a missing
    path, a subdirectory of a repo, or a missing git binary.
    """
    try:
        cp = _git(root, "rev-parse", "--show-toplevel")
    except (FileNotFoundError, ValueError):
        return False
    if cp.returncode != 0:
        return False
    top = _out(cp).strip()
    if not top:
        return False
    try:
        return os.path.realpath(top) == os.path.realpath(str(root))
    except OSError:
        return False


def _require_repo(root):
    """Raise FileNotFoundError (dispatcher -> exit 3) unless ``root`` is a repo."""
    if not is_git_root(root):
        raise FileNotFoundError("root is not a git checkout: %s" % root)


def _parse_git_iso(text):
    """Parse a git ``--date=iso`` timestamp into an aware datetime, or None.

    git ``--date=iso`` renders ``YYYY-MM-DD HH:MM:SS +ZZZZ``. ``iso-strict``
    (``...T...+ZZ:ZZ``) is accepted too, defensively.
    """
    s = (text or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return _dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _commit_meta(root, sha):
    """(committed_iso, subject) for one sha via ``git show -s``; ('', '') on miss."""
    cp = _git(root, "show", "-s", "--date=iso", "--pretty=%cd" + _US + "%s", sha)
    if cp.returncode != 0:
        return (None, None)
    text = _out(cp).strip()
    if not text:
        return (None, None)
    cd, _, subject = text.partition(_US)
    dt = _parse_git_iso(cd)
    committed = dt.isoformat() if dt else cd.strip() or None
    return (committed, subject.strip())


def commit_at(root, iso_date):
    """Newest commit at end-of-day ``iso_date`` -> ``(sha, committed_iso, subject)``.

    Implements ``git rev-list -1 --before='<iso> 23:59:59' HEAD`` -- the most
    recent commit whose commit date is at or before the last second of that
    calendar day. Returns ``(None, None, None)`` when the repo has no commit
    that early (e.g. a date before the first sweep).

    Raises FileNotFoundError when ``root`` is not a git checkout.
    """
    _require_repo(root)
    before = "%s 23:59:59" % iso_date
    cp = _git(root, "rev-list", "-1", "--before=%s" % before, "HEAD")
    sha = _out(cp).strip()
    if cp.returncode != 0 or not sha:
        return (None, None, None)
    committed, subject = _commit_meta(root, sha)
    return (sha, committed, subject)


def show_file(root, sha, relpath):
    """Raw bytes of ``relpath`` as it existed at ``sha``, or None if absent there.

    Implements ``git show <sha>:<relpath>``. A path that did not exist at that
    commit makes git exit non-zero -- reported as ``None`` rather than an error,
    so callers can fall back to ``result.last-good.json`` and note it.

    Raises FileNotFoundError when ``root`` is not a git checkout.
    """
    _require_repo(root)
    if not sha:
        return None
    cp = _git(root, "show", "%s:%s" % (sha, relpath))
    if cp.returncode != 0:
        return None
    return cp.stdout


def list_tree(root, sha, prefix=None):
    """Paths of every file tracked at ``sha`` (optionally under ``prefix``).

    Implements ``git ls-tree -r --name-only <sha> [-- <prefix>]`` -- a read-only
    listing of the commit's tree, used to discover which result-shaped snapshots
    a commit actually tracked (the canonical ``result.json`` is often gitignored,
    so the recoverable sweep lives at a differently-named tracked path). Returns
    an empty list when ``sha`` is falsy, the path is absent, or git errors --
    never raises for a missing path, so callers degrade gracefully.

    Raises FileNotFoundError when ``root`` is not a git checkout.
    """
    _require_repo(root)
    if not sha:
        return []
    argv = ["ls-tree", "-r", "--name-only", sha]
    if prefix:
        argv += ["--", prefix]
    cp = _git(root, *argv)
    if cp.returncode != 0:
        return []
    return [ln for ln in _out(cp).splitlines() if ln.strip()]


def sweep_log(root, since=None, until=None, limit=200):
    """Parsed commit log, newest first.

    Reads ``git log --date=iso`` and returns a list of dicts::

        {"sha": <full sha>, "datetime": <iso str>, "date": "YYYY-MM-DD",
         "subject": <commit subject>}

    ``since``/``until`` are optional ISO dates (``YYYY-MM-DD``) narrowing the
    window via git's ``--since``/``--until``; ``limit`` caps the count (git
    ``-n``). Callers that need exact single-day slices should additionally
    filter on the returned ``date`` field (timezone-independent).

    Raises FileNotFoundError when ``root`` is not a git checkout.
    """
    _require_repo(root)
    argv = ["log", "--date=iso", "--pretty=%H" + _US + "%cd" + _US + "%s"]
    if limit:
        argv += ["-n", str(int(limit))]
    if since:
        argv.append("--since=%s 00:00:00" % since)
    if until:
        argv.append("--until=%s 23:59:59" % until)
    argv.append("HEAD")
    cp = _git(root, *argv)
    if cp.returncode != 0:
        return []
    commits = []
    for line in _out(cp).splitlines():
        if not line.strip():
            continue
        parts = line.split(_US)
        if len(parts) < 3:
            continue
        sha, cd, subject = parts[0].strip(), parts[1].strip(), parts[2].strip()
        dt = _parse_git_iso(cd)
        commits.append(
            {
                "sha": sha,
                "datetime": dt.isoformat() if dt else (cd or None),
                "date": dt.date().isoformat() if dt else (cd[:10] or None),
                "subject": subject,
            }
        )
    return commits
