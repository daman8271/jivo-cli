"""Read-only explorer for note-shaped trees (the Obsidian vault + report runs).

Two primitives, both READ-ONLY (stat / scandir / open-for-read only):

- ``list_notes(base_dir, section=None, pattern=None)`` -> a newest-first list of
  ``{relpath, size, mtime}`` for every ``.md`` / ``.json`` / ``.csv`` file under
  ``base_dir`` (optionally narrowed to a ``section`` sub-directory), with an
  optional case-insensitive substring ``pattern`` filter over the relpath.
  A missing directory yields ``[]`` (never raises) so callers can degrade.

- ``read_note(base_dir, relpath)`` -> the raw text of one note, but FIRST it
  resolves the realpath and REFUSES anything that escapes ``base_dir`` by
  raising ``ValueError('path escapes root')`` (the dispatcher maps that to
  exit 2). This is the single traversal-guarded reader both commands use.

Also hosts two tiny presentation helpers (``human_size`` / ``table``) — sources
in this package already carry render helpers (see ``sweeps.table``), so the two
commands share one aligned-table renderer instead of each rolling its own.
"""

import datetime as _dt
import os

# The families that are text/data notes we are willing to list and cat.
NOTE_EXTS = (".md", ".json", ".csv")

# The vault sub-directories the CLI advertises as sections.
VAULT_SECTIONS = [
    "daily",
    "monthly",
    "competitor",
    "pricematch",
    "locations",
    "analysis",
    "platforms",
]


def _iso_mtime(st):
    """ISO-second mtime string for a stat result (sorts chronologically)."""
    return _dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec="seconds")


def list_notes(base_dir, section=None, pattern=None):
    """Newest-first note entries under base_dir (optionally a section subdir).

    Each entry is ``{"relpath": <relative to base_dir>, "size": int,
    "mtime": iso-second string}``. ``pattern`` is a case-insensitive substring
    match over the relpath. Ties in mtime break by relpath ascending. A missing
    root (or section subdir) returns an empty list rather than raising, so the
    command can note the absence instead of crashing.
    """
    root = base_dir if not section else os.path.join(base_dir, section)
    if not os.path.isdir(root):
        return []
    pat = pattern.lower() if pattern else None
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()  # deterministic traversal
        for name in filenames:
            if not name.lower().endswith(NOTE_EXTS):
                continue
            full = os.path.join(dirpath, name)
            try:
                st = os.stat(full)
            except OSError:
                continue  # vanished / unreadable — skip, never crash the listing
            rel = os.path.relpath(full, base_dir)
            if pat and pat not in rel.lower():
                continue
            entries.append(
                {"relpath": rel, "size": st.st_size, "mtime": _iso_mtime(st)}
            )
    # newest-first, ties by relpath ascending (stable double sort).
    entries.sort(key=lambda e: e["relpath"])
    entries.sort(key=lambda e: e["mtime"], reverse=True)
    return entries


def read_note(base_dir, relpath):
    """Return the raw text of a note under base_dir, guarded against traversal.

    Resolves the realpath of ``base_dir/relpath`` and refuses anything that
    escapes ``base_dir`` — an absolute relpath, a ``../`` climb, or a symlink
    pointing outside — by raising ``ValueError('path escapes root')``. A missing
    file surfaces as the usual ``FileNotFoundError`` (dispatcher -> exit 3); a
    relpath that resolves to a directory raises ``IsADirectoryError`` (also
    dispatcher -> exit 3) instead of letting ``open()`` spill a raw traceback.
    READ-ONLY: opened for reading only.
    """
    base_real = os.path.realpath(base_dir)
    target = os.path.realpath(os.path.join(base_dir, relpath))
    if target != base_real and not target.startswith(base_real + os.sep):
        raise ValueError("path escapes root")
    if os.path.isdir(target):
        # A directory is in-root but not a note; open() would raise
        # IsADirectoryError (an OSError the dispatcher does not otherwise map).
        # Raise it deliberately with a clean message so the CLI degrades to a
        # tidy "source is a directory" exit rather than a traceback.
        raise IsADirectoryError("not a readable note (is a directory): %s" % relpath)
    with open(target, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


# --- tiny shared presentation helpers -------------------------------------
def human_size(n):
    """Human-readable byte count (matches the files-command style)."""
    if n is None:
        return "-"
    f = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if f < 1024 or unit == "TB":
            return ("%d %s" % (int(f), unit)) if unit == "B" else ("%.1f %s" % (f, unit))
        f /= 1024.0
    return "%d B" % n


def table(headers, rows):
    """Left-aligned, space-padded columns (None/empty cells render blank)."""
    heads = [str(h) for h in headers]
    srows = [["" if c is None else str(c) for c in r] for r in rows]
    widths = [len(h) for h in heads]
    for r in srows:
        for i, c in enumerate(r):
            if i < len(widths):
                widths[i] = max(widths[i], len(c))

    def fmt(cells):
        return "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(cells))

    lines = [fmt(heads), "  ".join("-" * w for w in widths)]
    lines += [fmt(r) for r in srows]
    return "\n".join(lines)
