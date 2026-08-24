"""store — where a batch lives on disk.

Three files per batch, under `acc/_batches/<id>/` (gitignored — they carry
vendor names, bill references and amounts, and this repo is public):

  review-<id>.xlsx   what the operator opens
  sidecar.json       what the operator cannot edit: the payload for every row
  journal.jsonl      append-only, written before AND after every write

The sidecar is the authority. Everything that goes on the wire comes from it
except the four cells the review sheet lets a human change, so a row cannot be
turned into a different document by editing a spreadsheet. The journal is what
answers "what happened" after a crash or an exit 7, which is the moment nobody
can afford a guess.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import secrets
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping

SCHEMA = 1

COMPANY_TAGS = {
    "JIVO_OIL_HANADB": "OIL",
    "JIVO_MART_HANADB": "MART",
    "JIVO_BEVERAGES_HANADB": "BEV",
}


class SidecarError(RuntimeError):
    """The sidecar cannot be trusted — refuse rather than send from a guess."""


def company_tag(company_db: str | None) -> str:
    if company_db in COMPANY_TAGS:
        return COMPANY_TAGS[company_db]
    letters = re.sub(r"[^A-Z0-9]", "", (company_db or "DB").upper())
    return letters[:6] or "DB"


def new_batch_id(company_db: str | None, when: dt.datetime | None = None,
                 token: str | None = None) -> str:
    """B<yymmdd>-<OIL|MART|BEV>-<4 hex>.

    Short enough to travel inside a 254-character Comments field (that is how a
    run is found afterwards, in SAP's own search and in the write log), unique
    enough that two operators scanning the same company the same afternoon do
    not collide.
    """
    when = when or dt.datetime.now()
    suffix = (token or secrets.token_hex(2)).upper()[:4]
    return f"B{when:%y%m%d}-{company_tag(company_db)}-{suffix}"


def batch_dir(repo: Path | str, batch_id: str) -> Path:
    return Path(repo) / "acc" / "_batches" / batch_id


def workbook_name(batch_id: str) -> str:
    return f"review-{batch_id}.xlsx"


def sidecar_name(batch_id: str) -> str:
    """`sidecar-<id>.json`, never a bare `sidecar.json`.

    Two scans into one `--out` directory used to overwrite each other's sidecar
    while both workbooks survived: the second scan's file, the first scan's
    workbook, and a `send` that reads payloads belonging to different rows. The
    batch id is in the name so that cannot happen quietly.
    """
    return f"sidecar-{batch_id}.json"


def journal_name(batch_id: str) -> str:
    return f"journal-{batch_id}.jsonl"


def batch_id_from_workbook(workbook: Path | str) -> str | None:
    """`review-B240824-OIL-7F3A.xlsx` -> the id. Renamed files just give None."""
    m = re.fullmatch(r"review-(B\d{6}-[A-Z0-9]+-[A-Z0-9]{1,4})\.xlsx", Path(workbook).name)
    return m.group(1) if m else None


def find_sidecar_for(workbook: Path | str, batch_id: str | None = None,
                     repo: Path | str | None = None) -> Path | None:
    """Next to the workbook first, then the batch folder it was scanned into.

    Operators move workbooks — they mail them to themselves, or open them out of
    Downloads. Every place is checked before send refuses. The id-stamped name
    is preferred over the legacy bare `sidecar.json`, so a directory holding two
    batches resolves to the right one.
    """
    workbook = Path(workbook)
    batch_id = batch_id or batch_id_from_workbook(workbook)
    names = ([sidecar_name(batch_id)] if batch_id else []) + ["sidecar.json"]
    for name in names:
        beside = workbook.parent / name
        if beside.exists():
            return beside
    if batch_id and repo:
        home = batch_dir(repo, batch_id)
        for name in names:
            if (home / name).exists():
                return home / name
    return None


def write_atomic(path: Path, text: str) -> None:
    """Write via a temp file in the same directory, then rename.

    A sidecar half-written by a process that died is worse than no sidecar: send
    would read a truncated payload and believe it.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".sidecar-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


class Sidecar:
    def __init__(self, data: dict, path: Path | None = None) -> None:
        self.data = data
        self.path = Path(path) if path else None

    # -- construction ----------------------------------------------------

    @classmethod
    def new(cls, batch_id: str, company: str, login: str, host: str, scanned_at: str,
            scan_args: Mapping[str, Any] | None = None) -> "Sidecar":
        return cls({"schema": SCHEMA, "batch_id": batch_id, "company": company, "login": login,
                    "host": host, "scanned_at": scanned_at, "scan_args": dict(scan_args or {}),
                    "rows": {}})

    @classmethod
    def load(cls, path: Path | str) -> "Sidecar":
        path = Path(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            raise SidecarError(f"cannot read {path}: {e}") from e
        schema = data.get("schema")
        if schema != SCHEMA:
            raise SidecarError(
                f"{path} is sidecar schema {schema!r}, this build understands {SCHEMA} — "
                "re-scan rather than send from a file it may be reading wrong")
        return cls(data, path)

    # -- header ----------------------------------------------------------

    @property
    def batch_id(self) -> str:
        return self.data["batch_id"]

    @property
    def company(self) -> str:
        return self.data["company"]

    @property
    def login(self) -> str:
        return self.data.get("login", "?")

    @property
    def host(self) -> str:
        return self.data.get("host", "?")

    @property
    def scanned_at(self) -> str:
        return self.data.get("scanned_at", "")

    def age_days(self, now: dt.datetime | None = None) -> int:
        now = now or dt.datetime.now()
        try:
            scanned = dt.datetime.fromisoformat(self.scanned_at)
        except ValueError:
            return 10 ** 6                       # unreadable stamp = definitely too old
        if scanned.tzinfo and not now.tzinfo:
            scanned = scanned.replace(tzinfo=None)
        return max(0, (now - scanned).days)

    # -- rows ------------------------------------------------------------

    @property
    def rows(self) -> dict:
        return self.data["rows"]

    def row_keys(self) -> set[str]:
        return set(self.rows)

    def row(self, docentry: Any) -> dict:
        return self.rows[str(docentry)]

    def has_row(self, docentry: Any) -> bool:
        return str(docentry) in self.rows

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for row in self.rows.values():
            out[row["status"]] = out.get(row["status"], 0) + 1
        return out

    def add_row(self, docentry: Any, row: int, status: str, reasons: Iterable[str],
                locked: Mapping[str, Any], defaults: Mapping[str, Any],
                payload: Mapping[str, Any] | None, comments_base: str,
                expect: Mapping[str, Any], attachment_entry: Any,
                tds: Mapping[str, Any] | None, series: Mapping[str, Any] | None) -> dict:
        entry = {
            "row": row,
            "status": status,
            "reasons": list(reasons),
            "locked": dict(locked),
            "defaults": dict(defaults),
            "payload": dict(payload) if payload else None,
            "comments_base": comments_base,
            "expect": dict(expect),
            "attachment_entry": attachment_entry,
            "tds": dict(tds) if tds else None,
            "series": dict(series) if series else None,
            "outcome": None,
        }
        self.rows[str(docentry)] = entry
        return entry

    def update_outcome(self, docentry: Any, outcome: Mapping[str, Any] | None) -> None:
        """Record what happened to one row, and put it on disk before returning.

        Called immediately after every write. If the process dies on the next
        row, the fact that this one produced a draft has already survived.
        """
        key = str(docentry)
        if key not in self.rows:
            raise KeyError(f"row {key} is not in this batch")
        self.rows[key]["outcome"] = dict(outcome) if outcome else None
        if self.path:
            self.save()

    # -- persistence -----------------------------------------------------

    def save(self, path: Path | str | None = None) -> Path:
        target = Path(path) if path else self.path
        if target is None:
            raise SidecarError("no path to save the sidecar to")
        write_atomic(target, json.dumps(self.data, indent=1, ensure_ascii=False) + "\n")
        self.path = target
        return target


class Journal:
    """Append-only event log. One line per event, written before AND after a write."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def append(self, event: Mapping[str, Any]) -> dict:
        record = {"time": dt.datetime.now().astimezone().isoformat()}
        record.update(event)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            # A process killed mid-write leaves a line with no newline on it.
            # Appending onto that line glues two events into one string that is
            # neither, and the event lost that way is the one that says a draft
            # was created — the only record of it, at the only moment it matters.
            if self._needs_newline():
                fh.write("\n")
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        return record

    def _needs_newline(self) -> bool:
        """Does the file end mid-line? (Empty and missing files do not.)"""
        try:
            size = self.path.stat().st_size
            if not size:
                return False
            with self.path.open("rb") as fh:
                fh.seek(-1, os.SEEK_END)
                return fh.read(1) != b"\n"
        except OSError:
            return False

    def events(self) -> list[dict]:
        try:
            lines = self.path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return []
        out = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                # A crash mid-write leaves a partial last line. Reading the rest
                # is the whole point of coming here.
                continue
        return out

    # States that settle a row: after one of these, what SAP holds is known.
    # "unknown" is deliberately NOT among them — that is the exit-7 shape, and a
    # row whose answer never came back is exactly the row this method exists to
    # find. Recording it as resolved would hide the one case a person must look
    # at by hand.
    SETTLED = ("created", "rejected", "unreachable", "recovered", "unresolved")

    def in_flight(self) -> list[Any]:
        """Rows a write was started for and never finished.

        Two shapes end up here: a process that died between the two journal
        lines, and a write that came back exit 7. Both have to be resolved by
        LOOKING in SAP (`send --resume`), never by sending again.
        """
        started: list[Any] = []
        for e in self.events():
            if e.get("event") not in ("draft", "resume"):
                continue
            key = e.get("docentry")
            if e.get("state") == "sending":
                if key not in started:
                    started.append(key)
            elif e.get("state") in self.SETTLED and key in started:
                started.remove(key)
        return started
