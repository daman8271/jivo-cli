"""batch_send — the reviewed workbook goes back to SAP, one draft per approved row.

This is the half that writes, so almost all of it is about NOT writing:

  * `--yes` is handed to `sapb1` in exactly one place, inside `if sending:`.
    Every other path runs `--dry-run`. `sapb1` itself refuses a write without
    `--yes` when stdin is not a terminal, so a batch physically cannot post by
    accident — test_send.py pins both halves of that.
  * Nothing on the wire comes from the spreadsheet except the four cells a
    reviewer is allowed to change (V approve, W TDS, X bill date, Y vendor ref,
    Z note). Everything else comes from the sidecar, and every locked cell is
    compared against it first — a changed grey cell makes the row refuse.
  * SAP is asked again, per row, immediately before its draft is sent: is the
    goods receipt still open, is the quantity still what we costed, has somebody
    keyed this bill in the meantime. A scan is a photograph; Accounts keeps
    working after it was taken.
  * A row whose answer never came back (exit 7) HALTS the run. It is never
    re-sent from this batch — `--resume` looks for what may exist first.

Outcomes a row can end with, and what each means to the operator:

  SKIPPED             not approved (V is not "yes")
  REFUSED-STATUS      approved, but the scan had already held it
  TAMPERED            a locked cell no longer matches the sidecar
  INVALID-INPUT       an editable cell is empty or unusable
  ALREADY-CREATED     this batch already made that draft
  STALE               SAP has moved on (GRPO closed, quantity changed, vendor frozen)
  STALE-DUPLICATE     somebody keyed this bill between the scan and now
  PREVIEWED           dry run only — nothing was sent
  CREATED             draft made, read back, nothing to flag
  CREATED-WITH-GAPS   draft made, and something needs a human in the client
  CREATED-RECOVERED   --resume found the draft an unknown outcome had left behind
  REJECTED            SAP said no. Nothing was committed; fix it and run again
  UNKNOWN             sent, no answer. GO LOOK. Never re-sent from here
  UNKNOWN-UNRESOLVED  --resume looked and found nothing; a person decides
  FOREIGN-DRAFT-FOUND --resume found a draft for this bill that this batch did
                      not make. It is not adopted, not patched, not re-sent
  NOT-ATTEMPTED       the run halted before this row
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import precheck as apprecheck
from . import readback as apreadback
from . import rules, store, xlsx
from .context import DRAFT_PAGE_SIZE, POSTED_SELECT
from .sap import (SapAuth, SapCli, SapConfig, SapError, SapRejected, SapUnknownOutcome,
                  SapUnreachable, find_repo, odata_str, or_filter)

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# -- outcomes ---------------------------------------------------------------

SKIPPED = "SKIPPED"
REFUSED_STATUS = "REFUSED-STATUS"
TAMPERED = "TAMPERED"
INVALID_INPUT = "INVALID-INPUT"
ALREADY_CREATED = "ALREADY-CREATED"
STALE = "STALE"
STALE_DUPLICATE = "STALE-DUPLICATE"
PREVIEWED = "PREVIEWED"
CREATED = "CREATED"
CREATED_WITH_GAPS = "CREATED-WITH-GAPS"
CREATED_RECOVERED = "CREATED-RECOVERED"
REJECTED = "REJECTED"
UNKNOWN = "UNKNOWN"
UNKNOWN_UNRESOLVED = "UNKNOWN-UNRESOLVED"
FOREIGN_DRAFT_FOUND = "FOREIGN-DRAFT-FOUND"
NOT_ATTEMPTED = "NOT-ATTEMPTED"

# Outcomes that mean a draft exists in SAP.
MADE_A_DRAFT = (CREATED, CREATED_WITH_GAPS, CREATED_RECOVERED)
# Outcomes that are fine to finish a run on.
CLEAN = (SKIPPED, PREVIEWED, CREATED, CREATED_RECOVERED, ALREADY_CREATED)

DOCTYPE = "purchase-invoice"

# Column indexes on the Review sheet (A=0).
COL = {letter: xlsx.column_index(letter) for letter in
       ("A", "B", "C", "D", "E", "F", "N", "T", "U", "V", "W", "X", "Y", "Z")}

# How far back a vendor's bill date may sit from the goods-receipt date before
# it stops looking like the same transaction. 120 days is deliberately loose:
# the pile has GRPOs from last October, and the point is to catch a typed year,
# not to argue with Accounts about an old bill.
MAX_BILL_AGE_DAYS = 120
MAX_REF_LEN = 100

# How far back the vendor's POSTED invoices are swept when looking for the same
# bill spelled another way. The server-side filter can only match a reference
# exactly, so the variants have to be compared in Python, which means fetching
# rows — and a vendor JIVO has bought from for ten years has thousands. Bounded
# at the goods receipt's date minus this, which comfortably covers the bill
# window (a bill more than MAX_BILL_AGE_DAYS from its GRPO is refused anyway)
# without dragging a decade of history over the bridge for every row.
DUP_WINDOW_DAYS = 400


@dataclass
class RowResult:
    row: int
    docentry: Any
    outcome: str
    message: str = ""
    vendor: str = ""
    vendor_name: str = ""
    ref: str = ""
    gross: float = 0.0
    docnum: Any = ""
    draft_entry: Any = None
    draft_num: Any = None
    attachment: str = ""
    wtamount: Any = ""
    flags: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"row": self.row, "docentry": self.docentry, "outcome": self.outcome,
                "message": self.message, "draft_entry": self.draft_entry,
                "draft_num": self.draft_num, "flags": list(self.flags)}


def _money(value: Any) -> float:
    """A money cell as a number. Anything unreadable is 0 — this figure is for
    the console and the results sheet, never for the payload."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


class Refused(RuntimeError):
    """A precondition failed. Nothing was contacted; exit 2."""


class _Unread:
    """Sentinel: this has not been looked up yet, as opposed to "it is None"."""


_UNREAD = _Unread()


# --------------------------------------------------------------------------
# the command
# --------------------------------------------------------------------------

def run_send(args, sap: SapCli | None = None, today: dt.date | None = None,
             now: dt.datetime | None = None, repo: Path | str | None = None) -> int:
    today = today or dt.date.today()
    now = now or dt.datetime.now()
    repo = Path(repo) if repo else find_repo()
    quiet = bool(getattr(args, "quiet", False))

    def say(*parts):
        if not quiet:
            print(*parts)

    # --dry-run wins over --yes. Somebody typing both wants the preview.
    sending = bool(getattr(args, "yes", False)) and not bool(getattr(args, "dry_run", False))
    resume = bool(getattr(args, "resume", False))

    # -- preconditions: all of these happen before SAP is touched at all ----
    try:
        book_path, sheet, sidecar = _open_batch(args, repo, now)
    except Refused as e:
        print(f"acc batch send: {e}", file=sys.stderr)
        return 2

    if sap is None:
        try:
            sap = SapCli(repo=repo, company=sidecar.company,
                         env_file=getattr(args, "env", None), allow_writes=True)
        except SapConfig as e:
            print(f"acc batch send: {e}", file=sys.stderr)
            return 3

    if sap.company_db != sidecar.company:
        print(f"acc batch send: this workbook was scanned against {sidecar.company} but the CLI "
              f"resolves to {sap.company_db}. Sending it would create the drafts in the wrong "
              "company's books. Pass --company/--env for the right one, or re-scan.",
              file=sys.stderr)
        return 2

    out_dir = book_path.parent
    journal = store.Journal(out_dir / store.journal_name(sidecar.batch_id))
    payload_dir = out_dir / "payloads"
    run_stamp = now.strftime("%Y%m%dT%H%M%S")

    say(f"== acc batch send · {sidecar.batch_id} · {sidecar.company} · login {sap.user} "
        f"· host {sap.route}")
    say(f"   env       {sap.env_path or '(sap-b1/cli/.env)'}")
    if getattr(sap, "default_company_db", sidecar.company) != sidecar.company:
        # Reachable in a real run: send names the company itself (from the
        # sidecar), so the drafts go to the right books whatever the env says —
        # but an env pointing at another company usually means the wrong env
        # file, and that decides the LOGIN too.
        say(f"   NOTE      {sap.env_path or 'your .env'} defaults to "
            f"{sap.default_company_db}; this batch is being sent against "
            f"{sidecar.company}, which is the company it was scanned from.")
    say(f"   workbook  {book_path}")
    say(f"   sidecar   {sidecar.path}  (scanned {sidecar.scanned_at[:19]}, "
        f"{sidecar.age_days(now)} day(s) ago)")
    say("   MODE      SENDING — drafts will be created" if sending else
        "   MODE      preview only — nothing will be sent (add --yes to send)")
    say("")

    journal.append({"event": "send-start", "batch_id": sidecar.batch_id, "run": run_stamp,
                    "sending": sending, "resume": resume, "login": sap.user,
                    "host": sap.route, "workbook": str(book_path)})

    ctx = _SendContext(sap)
    results: list[RowResult] = []
    resolved: dict[str, RowResult] = {}       # rows settled by the resume pass
    halted = False
    exit_code = 0
    rows = _data_rows(sheet)

    def row_result(cells) -> RowResult:
        """The shell of a result. Nothing here may raise on a junk cell: column A
        is neither locked nor editable, so `one` typed into it used to end the
        whole run in a traceback — after some rows had already been drafted."""
        return RowResult(row=_row_number(cells[COL["A"]]), docentry=cells[COL["C"]],
                         vendor=str(cells[COL["E"]] or ""),
                         vendor_name=str(cells[COL["F"]] or ""),
                         ref=str(cells[COL["Y"]] or "").strip(), docnum=cells[COL["B"]],
                         gross=_money(cells[COL["N"]]), outcome=SKIPPED)

    def halt(code: int, message: str) -> None:
        nonlocal halted, exit_code
        halted, exit_code = True, code
        made = [r for r in results if r.outcome in MADE_A_DRAFT]
        if made:
            # Never "nothing was sent" once something was. The drafts are named
            # so the operator can go and look at exactly those.
            message += ("\n  Drafts this run had ALREADY created, which exist in SAP: "
                        + ", ".join(str(r.draft_entry) for r in made))
        print(f"\nacc batch send: {message}", file=sys.stderr)

    try:
        # -- resume comes FIRST -----------------------------------------------
        #
        # A run that sends the other rows and then resolves the unknown one has
        # the order backwards: the unknown row may be a draft that exists, and
        # until somebody knows, this batch has no business adding to the pile.
        # Resolve, then decide whether the rest of the run may go ahead at all.
        if resume:
            for cells in rows:
                entry = sidecar.rows.get(str(cells[COL["C"]])) or {}
                if ((entry.get("outcome") or {}).get("state")) != UNKNOWN:
                    continue
                res = row_result(cells)
                res.outcome = UNKNOWN
                try:
                    _resolve_unknown_row(res, sidecar, ctx, sap, journal, run_stamp, sending)
                except (SapUnreachable, SapAuth, SapConfig) as e:
                    res.message = f"could not look this row up in SAP: {str(e).splitlines()[0]}"
                    res.outcome = UNKNOWN_UNRESOLVED
                results.append(res)
                resolved[str(res.docentry)] = res
                _say_row(say, res)

            blocked = [r for r in results if r.outcome in (UNKNOWN_UNRESOLVED,
                                                           FOREIGN_DRAFT_FOUND)]
            if blocked:
                unresolved = [r for r in blocked if r.outcome == UNKNOWN_UNRESOLVED]
                halt(7 if unresolved else 1,
                     f"{len(blocked)} row(s) this batch cannot account for "
                     f"({', '.join(str(r.docentry) for r in blocked)}). Nothing else was sent. "
                     + ("A draft may exist for one of them: look in Document Drafts before "
                        "anything from this batch goes out again."
                        if unresolved else
                        "The draft that carries that bill was made by somebody else — decide "
                        "what to do with it in the client, then run again."))

        # -- the rows themselves ------------------------------------------------
        for cells in rows:
            docentry = cells[COL["C"]]
            if str(docentry) in resolved:
                continue                       # settled by the resume pass above
            entry = sidecar.rows.get(str(docentry))
            res = row_result(cells)

            if halted:
                approved = str(cells[COL["V"]] or "").strip().lower() == "yes"
                res.outcome = NOT_ATTEMPTED if approved else SKIPPED
                if approved:
                    res.message = "the run stopped before this row was reached"
                results.append(res)
                continue

            try:
                _decide_row(res, cells, entry, sidecar, ctx, sap, today, resume)
            except SapUnreachable as e:
                res.outcome = STALE
                res.message = f"could not re-check this row against SAP: {str(e).splitlines()[0]}"
                results.append(res)
                _say_row(say, res)
                halt(4, "SAP became unreachable. This row was NOT sent, and nothing after it "
                        "was attempted.")
                continue
            except (SapAuth, SapConfig) as e:
                res.outcome = STALE
                res.message = f"SAP would not let us in: {str(e).splitlines()[0]}"
                results.append(res)
                _say_row(say, res)
                halt(3, f"SAP would not let us in — {str(e).splitlines()[0]}")
                continue
            except Exception as e:             # noqa: BLE001 - see row_result
                # A cell nobody anticipated. One row is refused; the run goes on
                # and, above all, still writes its results and closes its journal.
                res.outcome = INVALID_INPUT
                res.message = (f"this row could not be read: {type(e).__name__}: {e}. "
                               "Check the cells against the sidecar, or re-scan.")
                results.append(res)
                _say_row(say, res)
                continue

            if res.outcome != "PENDING":
                results.append(res)
                _say_row(say, res)
                if res.outcome == UNKNOWN:
                    # Only reachable without --resume: an unresolved row from an
                    # earlier run. Nothing more may be sent from this batch until
                    # a person has looked (the plan's rule, and the only one that
                    # keeps a lost write from becoming a second invoice).
                    halt(7, "a row of this batch was sent by an earlier run and never answered. "
                            "Look in Document Drafts, then run again with --resume.")
                continue

            # -- the row is good: build exactly what would go on the wire -------
            payload = _finalize(entry, cells, sidecar.batch_id, ref=res.ref)
            payload_dir.mkdir(parents=True, exist_ok=True)
            payload_file = payload_dir / f"{docentry}.json"
            payload_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                                    encoding="utf-8")

            try:
                preview = sap.draft(DOCTYPE, data_file=payload_file, dry_run=True)
            except SapError as e:
                res.outcome = REJECTED
                res.message = f"the dry run itself was refused: {str(e).splitlines()[0]}"
                results.append(res)
                _say_row(say, res)
                continue
            _write_dryrun(out_dir / f"dryrun-{run_stamp}.txt", docentry, payload, preview)

            if not sending:
                res.outcome = PREVIEWED
                res.message = (f"would draft {rules.inr(res.gross)} · ref "
                               f"{payload['NumAtCard']!r} · TaxDate {payload['TaxDate']} "
                               f"· WTLiable {payload['DocumentLines'][0].get('WTLiable')}")
                results.append(res)
                _say_row(say, res)
                continue

            # ------------------------------------------------------------------
            # THE ONLY PLACE THIS PROGRAM WRITES. `--yes` exists nowhere else.
            # ------------------------------------------------------------------
            journal.append({"event": "draft", "state": "sending", "batch_id": sidecar.batch_id,
                            "run": run_stamp, "docentry": docentry, "row": res.row,
                            "cardcode": res.vendor, "ref": payload["NumAtCard"],
                            "gross": res.gross, "payload_file": str(payload_file)})
            try:
                created = sap.draft(DOCTYPE, data_file=payload_file, yes=True)
            except SapRejected as e:
                res.outcome = REJECTED
                res.message = str(e).splitlines()[0]
                journal.append({"event": "draft", "state": "rejected", "docentry": docentry,
                                "run": run_stamp, "message": res.message})
                sidecar.update_outcome(docentry, {"state": REJECTED, "message": res.message,
                                                  "run": run_stamp})
                results.append(res)
                _say_row(say, res)
                continue                   # nothing was committed: the next row is safe
            except SapUnreachable as e:
                # Exit 5 is raised by the CLI when it cannot connect at all, so
                # this request never went out and nothing was committed.
                res.outcome = STALE
                res.message = f"could not reach SAP to send this row: {str(e).splitlines()[0]}"
                journal.append({"event": "draft", "state": "unreachable", "docentry": docentry,
                                "run": run_stamp, "message": res.message})
                results.append(res)
                _say_row(say, res)
                halt(4, "SAP became unreachable while sending. This row never went out.")
                continue
            except SapError as e:
                # SapUnknownOutcome and everything else. sap._send already turns
                # every code it cannot read as "nothing was sent" into an unknown
                # outcome; the ones that reach here as another class (usage,
                # config, auth) are conditions this code did not plan for at a
                # write, and a write nobody planned for is not evidence that
                # nothing happened. Halt and go look.
                res.outcome = UNKNOWN
                res.message = str(e).splitlines()[0]
                if not isinstance(e, SapUnknownOutcome):
                    res.message = (f"{type(e).__name__} while sending: {res.message} — this "
                                   "build cannot prove nothing was sent")
                journal.append({"event": "draft", "state": "unknown", "docentry": docentry,
                                "run": run_stamp, "message": res.message,
                                "error": type(e).__name__})
                sidecar.update_outcome(docentry, {"state": UNKNOWN, "message": res.message,
                                                  "run": run_stamp})
                results.append(res)
                _say_row(say, res)
                halt(7, "a write went out and this run cannot say what happened to it. "
                        "Do NOT re-run it: look in Document Drafts, then use --resume.")
                continue

            if not _record_created(res, created):
                res.outcome = UNKNOWN
                res.message = ("SAP accepted the write and the answer carried no DocEntry "
                               f"({created!r}) — the draft may exist and this run cannot say "
                               "which one it is. Do NOT re-run it: look in Document Drafts, "
                               "then use --resume.")
                journal.append({"event": "draft", "state": "unknown", "docentry": docentry,
                                "run": run_stamp, "message": res.message,
                                "answer": repr(created)[:200]})
                sidecar.update_outcome(docentry, {"state": UNKNOWN, "message": res.message,
                                                  "run": run_stamp})
                results.append(res)
                _say_row(say, res)
                halt(7, "a draft was accepted without a DocEntry. Do NOT re-run it: look in "
                        "Document Drafts, then use --resume.")
                continue

            journal.append({"event": "draft", "state": "created", "docentry": docentry,
                            "run": run_stamp, "draft_entry": res.draft_entry,
                            "draft_num": res.draft_num})
            sidecar.update_outcome(docentry, {"state": CREATED, "draft_entry": res.draft_entry,
                                              "draft_num": res.draft_num, "run": run_stamp})

            _attach_and_read_back(res, entry, cells, sap, journal, run_stamp)
            results.append(res)
            _say_row(say, res)
    finally:
        # Whatever happened — a halt, an unhandled bug, a Ctrl-C — the run leaves
        # the two records behind that answer "what did it do": the results
        # workbook and the closing journal line. They are worth most precisely
        # when the run did not finish cleanly.
        summary = _summarize(results)
        # Only the rows that did something: on a 331-row workbook where 327 were
        # not approved, listing every SKIPPED row makes a 40 KB journal line that
        # hides the four that matter. The results workbook holds the full picture.
        journal.append({"event": "send-end", "run": run_stamp, "sending": sending,
                        "counts": summary,
                        "rows": [r.as_dict() for r in results if r.outcome != SKIPPED]})
        book = _write_results(out_dir, sidecar.batch_id, run_stamp, results)
        _report(say, results, summary, sidecar, sap, book, sending, halted)

    if exit_code:
        return exit_code
    return 0 if all(r.outcome in CLEAN for r in results) else 1


def _row_number(value: Any) -> int:
    """Column A as a row number, or 0. It is a label, never a decision."""
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return 0


# --------------------------------------------------------------------------
# preconditions
# --------------------------------------------------------------------------

def _open_batch(args, repo: Path, now: dt.datetime):
    """The workbook, its Review sheet and its sidecar — or Refused, with a reason."""
    book_path = Path(getattr(args, "workbook", "") or "")
    if not book_path.exists():
        raise Refused(f"no such workbook: {book_path}")
    try:
        sheets = xlsx.read_workbook(book_path)
    except Exception as e:
        raise Refused(f"cannot read {book_path.name} as a workbook ({e}). Save it as .xlsx from "
                      "Excel — .xls and .csv cannot carry the review sheet.") from e
    if "Review" not in sheets:
        raise Refused(f"{book_path.name} has no 'Review' sheet — is it the workbook `acc batch "
                      "scan` produced?")
    sheet = sheets["Review"]
    if len(sheet) < 2:
        raise Refused(f"{book_path.name} has no rows to send")

    batch_id = _batch_id_from_about(sheets.get("About") or [])
    if not batch_id:
        batch_id = store.batch_id_from_workbook(book_path)
    if not batch_id:
        raise Refused("cannot find the batch id (About sheet, row 'batch_id'). Without it there "
                      "is no way to know which sidecar belongs to this workbook.")

    path = store.find_sidecar_for(book_path, batch_id=batch_id, repo=repo)
    if not path:
        raise Refused(
            f"no sidecar for {batch_id}. It holds the payload for every row and nothing can be "
            f"sent without it — look for {store.sidecar_name(batch_id)} next to the workbook or "
            f"in {store.batch_dir(repo, batch_id)}, or re-scan.")
    try:
        sidecar = store.Sidecar.load(path)
    except store.SidecarError as e:
        raise Refused(str(e)) from e

    if sidecar.batch_id != batch_id:
        raise Refused(f"the workbook says batch {batch_id} and the sidecar beside it says "
                      f"{sidecar.batch_id} — they are different runs. Put them back together "
                      "or re-scan.")

    sheet_keys = {str(r[COL["C"]]) for r in _data_rows(sheet)}
    if sheet_keys != sidecar.row_keys():
        missing = sorted(sidecar.row_keys() - sheet_keys)
        extra = sorted(sheet_keys - sidecar.row_keys())
        raise Refused(
            "the workbook's rows are not the batch's rows — rows were added or deleted after "
            f"the scan (missing from the sheet: {missing[:5]}; not in the batch: {extra[:5]}). "
            "Re-scan rather than send from a file that has been rearranged.")

    max_age = int(getattr(args, "max_age_days", 3) or 0)
    age = sidecar.age_days(now)
    if max_age and age > max_age:
        raise Refused(
            f"this batch was scanned {age} days ago (limit {max_age}). Accounts has been keying "
            "bills since then, so half of what it says about SAP may no longer be true. "
            "Re-scan — it is a read, it costs a minute.")
    return book_path, sheet, sidecar


def _batch_id_from_about(about: Sequence[Sequence[Any]]) -> str | None:
    for row in about:
        if row and str(row[0]).strip() == "batch_id" and len(row) > 1:
            return str(row[1]).strip() or None
    return None


def _data_rows(sheet: Sequence[Sequence[Any]]) -> list[list]:
    """Rows under the header that carry a GRPO DocEntry."""
    out = []
    for row in sheet[1:]:
        if len(row) > COL["Z"] and str(row[COL["C"]] or "").strip():
            out.append(list(row))
    return out


# --------------------------------------------------------------------------
# per row
# --------------------------------------------------------------------------

def _decide_row(res: RowResult, cells: Sequence[Any], entry: Mapping[str, Any] | None,
                sidecar: store.Sidecar, ctx: "_SendContext", sap: SapCli,
                today: dt.date, resume: bool) -> None:
    """Everything that can refuse a row. Sets res.outcome to PENDING if none does."""
    if entry is None:                       # cannot happen: the key sets matched
        res.outcome = REFUSED_STATUS
        res.message = "this row is not in the sidecar"
        return

    if str(cells[COL["V"]] or "").strip().lower() != "yes":
        res.outcome = SKIPPED
        res.message = "not approved"
        return

    if entry["status"] != apprecheck.READY:
        res.outcome = REFUSED_STATUS
        res.message = (f"the scan held this row as {entry['status']}: "
                       f"{'; '.join(entry.get('reasons') or []) or 'see the Reason column'}")
        return

    tampered = _tamper(cells, entry)
    if tampered:
        res.outcome = TAMPERED
        res.message = "; ".join(tampered)
        return

    # Column A is the row label — neither locked nor editable, so nothing else
    # checks it. Junk there does not change the document, but it is evidence the
    # sheet was edited outside the yellow cells, and the operator should see it.
    if not res.row and str(cells[COL["A"]] or "").strip() not in ("", "0"):
        res.flags.append(f"the row number in column A is {cells[COL['A']]!r}, which is not a "
                         "number — this sheet has been edited outside the yellow cells")

    outcome = entry.get("outcome") or {}
    state = outcome.get("state")
    if state in MADE_A_DRAFT:
        res.outcome = ALREADY_CREATED
        res.draft_entry = outcome.get("draft_entry")
        res.draft_num = outcome.get("draft_num")
        res.message = f"this batch already made draft {res.draft_entry}"
        return
    if state == UNKNOWN:
        # With --resume this row was already settled by the pass that runs
        # before this one, so it never reaches here; without it, the row (and
        # the rest of the batch) stops until a person has looked.
        res.outcome = UNKNOWN
        res.message = ("a previous run sent this row and never got an answer. Look in Document "
                       "Drafts, then run again with --resume. It will not be re-sent from here.")
        return

    # The reference is resolved ONCE, here, and everything downstream — the
    # validation, the duplicate sweep and the payload — uses that one value.
    # They used to read the cell separately, so a cell Excel had re-typed could
    # be checked in one spelling and sent in another.
    raw_ref = cells[COL["Y"]]
    if isinstance(raw_ref, (int, float)) and not isinstance(raw_ref, bool):
        # Excel re-typed the reference as a number. Neither the number nor the
        # scan's old value is what the reviewer meant to send, so nobody guesses:
        # the row is refused until the cell is text again and retyped from the bill.
        res.outcome = INVALID_INPUT
        res.message = (f"column Y came back from Excel as the number {raw_ref!r} — format the "
                       "cell as Text, retype the vendor reference from the bill, save, and send again")
        return
    res.ref, ref_flag = rules.cell_text(raw_ref, (entry.get("defaults") or {}).get("Y"))
    if ref_flag:
        res.flags.append(ref_flag)

    invalid = _validate_inputs(cells, entry, today, ref=res.ref)
    if invalid:
        res.outcome = INVALID_INPUT
        res.message = "; ".join(invalid)
        return

    stale = _revalidate(res, entry, cells, ctx, sap)
    if stale:
        res.outcome, res.message = stale
        return

    res.outcome = "PENDING"


def _tamper(cells: Sequence[Any], entry: Mapping[str, Any]) -> list[str]:
    """Every locked cell that no longer matches the sidecar, named by address."""
    problems = []
    for letter, expected in sorted((entry.get("locked") or {}).items()):
        index = xlsx.column_index(letter)
        actual = cells[index] if index < len(cells) else ""
        if not xlsx.same_cell(expected, actual):
            problems.append(f"cell {letter}{entry['row'] + 1} was {expected!r} at scan time and "
                            f"is {actual!r} now")
    return problems


def _validate_inputs(cells: Sequence[Any], entry: Mapping[str, Any], today: dt.date,
                     ref: str | None = None) -> list[str]:
    """The four editable cells, checked before anything is built from them."""
    problems = []

    tds = str(cells[COL["W"]] or "").strip().lower()
    if tds not in ("yes", "no"):
        problems.append("TDS (column W) must say yes or no — it is "
                        f"{str(cells[COL['W']] or '')!r}. The scan left it blank because the "
                        "evidence contradicted itself; read the TDS evidence column and answer it")

    ref = ref if ref is not None else rules.cell_text(
        cells[COL["Y"]], (entry.get("defaults") or {}).get("Y"))[0]
    if not ref:
        problems.append("the vendor reference (column Y) is empty — NumAtCard is how this bill "
                        "is found again, by us and by GST")
    elif len(ref) > MAX_REF_LEN:
        problems.append(f"the vendor reference (column Y) is {len(ref)} characters; SAP takes "
                        f"{MAX_REF_LEN}")

    raw = cells[COL["X"]]
    try:
        bill_date = rules.parse_sheet_date(raw)
    except ValueError as e:
        problems.append(f"the vendor bill date (column X) cannot be read: {e}")
        return problems
    if bill_date is None:
        problems.append("the vendor bill date (column X) is empty — it is the TaxDate on the "
                        "invoice and GST is filed on it")
        return problems
    if bill_date > today:
        problems.append(f"the vendor bill date {bill_date.isoformat()} is in the future")
    docdate = (entry.get("payload") or {}).get("DocDate")
    if docdate:
        floor = rules.as_date(docdate) - dt.timedelta(days=MAX_BILL_AGE_DAYS)
        if bill_date < floor:
            problems.append(f"the vendor bill date {bill_date.isoformat()} is more than "
                            f"{MAX_BILL_AGE_DAYS} days before the goods receipt ({docdate}) — "
                            "check the year")
    return problems


def _finalize(entry: Mapping[str, Any], cells: Sequence[Any], batch_id: str,
              ref: str | None = None) -> dict:
    """The sidecar's payload plus the four send-time fields. Nothing else."""
    note = str(cells[COL["Z"]] or "").strip()
    comments = rules.build_comments(entry.get("comments_base") or "", note=note, tag=batch_id)
    wtliable = "tYES" if str(cells[COL["W"]]).strip().lower() == "yes" else "tNO"
    payload = rules.finalize_payload(
        entry["payload"],
        num_at_card=ref if ref is not None else rules.cell_text(
            cells[COL["Y"]], (entry.get("defaults") or {}).get("Y"))[0],
        tax_date=rules.parse_sheet_date(cells[COL["X"]]),
        wtliable=wtliable,
        comments=comments)
    return payload


# --------------------------------------------------------------------------
# live re-validation (R5, R6, R7)
# --------------------------------------------------------------------------

class _SendContext:
    """The reads send makes, with the ones worth remembering remembered.

    Every sweep that looks for a duplicate passes `all=True`. `sapb1 query`
    defaults to `--top 20` (internal/cli/listcmd.go), so without it the question
    "is this bill already drafted for this vendor" was answered from the first
    twenty rows of the answer. Oil carries 1,053 open A/P drafts; a vendor with
    two dozen is ordinary, and the duplicate is as likely to be the 25th as the
    2nd. A capped duplicate check is worse than none: it reads like a check.

    The duplicate sweeps are deliberately NOT cached. Two approved rows can carry
    the same reference after a reviewer edits column Y, and the second one has to
    be able to see the draft the first one just made, seconds earlier.
    """

    def __init__(self, sap: SapCli) -> None:
        self.sap = sap
        self._vendors: dict[str, dict] = {}
        self._login_key: Any = _UNREAD
        self.reads = 0

    def grpo(self, docentry: Any) -> dict | None:
        rows = self._query("PurchaseDeliveryNotes", filter=f"DocEntry eq {int(docentry)}")
        return rows[0] if rows else None

    def vendor(self, card: str) -> dict:
        if card not in self._vendors:
            rows = self._query("BusinessPartners", filter=f"CardCode eq {odata_str(card)}",
                               select="CardCode,CardName,Valid,Frozen")
            self._vendors[card] = rows[0] if rows else {}
        return self._vendors[card]

    def login_key(self) -> Any:
        """This login's UserSign (OUSR.InternalKey), or None if it cannot be read.

        Only --resume needs it, so it is fetched only when --resume asks. None
        means "no evidence available", never "matches" — see rules.adoption_evidence.
        """
        if self._login_key is _UNREAD:
            self._login_key = None
            user = getattr(self.sap, "user", None)
            if user and user != "?":
                try:
                    rows = self._query("Users", filter=f"UserCode eq {odata_str(user)}",
                                       select="InternalKey,UserCode,UserName")
                except SapError:
                    rows = []
                if rows:
                    self._login_key = rows[0].get("InternalKey")
        return self._login_key

    def posted_with_ref(self, ref: str) -> list[dict]:
        variants = rules.ref_variants(ref)
        if not variants:
            return []
        return self._query(
            "PurchaseInvoices",
            filter=f"({or_filter('NumAtCard', variants)}) and Cancelled eq 'tNO'",
            select=POSTED_SELECT, all=True)

    def posted_for_vendor(self, card: str, since: Any = None) -> list[dict]:
        """This vendor's posted A/P invoices, for a reference comparison in Python.

        `NumAtCard eq '2633100542'` does not match `.2633100542`, and Accounts
        types both. Bounded by DUP_WINDOW_DAYS — see the constant.
        """
        window = ""
        if since:
            window = f"DocDate ge '{rules.as_date(since).isoformat()}' and "
        return self._query(
            "PurchaseInvoices",
            filter=f"{window}CardCode eq {odata_str(card)} and Cancelled eq 'tNO'",
            select=POSTED_SELECT, all=True, page_size=200)

    def open_drafts_with_ref(self, ref: str) -> list[dict]:
        variants = rules.ref_variants(ref)
        if not variants:
            return []
        return self._query(
            "Drafts",
            filter=("DocObjectCode eq 'oPurchaseInvoices' and DocumentStatus eq 'bost_Open' "
                    f"and ({or_filter('NumAtCard', variants)})"),
            all=True, page_size=DRAFT_PAGE_SIZE)

    def open_drafts_for_vendor(self, card: str) -> list[dict]:
        return self._query(
            "Drafts",
            filter=("DocObjectCode eq 'oPurchaseInvoices' and DocumentStatus eq 'bost_Open' "
                    f"and CardCode eq {odata_str(card)}"),
            all=True, page_size=DRAFT_PAGE_SIZE)

    def _query(self, entity: str, **kw: Any) -> list[dict]:
        self.reads += 1
        return self.sap.query(entity, **kw)


def _revalidate(res: RowResult, entry: Mapping[str, Any], cells: Sequence[Any],
                ctx: _SendContext, sap: SapCli) -> tuple[str, str] | None:
    """Ask SAP again. A scan is a photograph; people kept working after it."""
    payload = entry["payload"]
    docentry = res.docentry

    # R5 — the goods receipt itself
    grpo = ctx.grpo(docentry)
    if not grpo:
        return STALE, f"GRPO DocEntry {docentry} is no longer readable in SAP"
    if grpo.get("Cancelled") != "tNO":
        return STALE, f"GRPO {grpo.get('DocNum')} has been cancelled since the scan"
    if grpo.get("DocumentStatus") != "bost_Open":
        return STALE, (f"GRPO {grpo.get('DocNum')} is now {grpo.get('DocumentStatus')} — "
                       "somebody invoiced it after the scan")
    if (grpo.get("CardCode") or "") != payload["CardCode"]:
        return STALE, (f"GRPO {grpo.get('DocNum')} is now against {grpo.get('CardCode')}, "
                       f"not {payload['CardCode']}")

    by_line = {l.get("LineNum"): l for l in (grpo.get("DocumentLines") or [])}
    for line in payload["DocumentLines"]:
        live = by_line.get(line["BaseLine"])
        if live is None:
            return STALE, f"line {line['BaseLine']} is no longer on GRPO {grpo.get('DocNum')}"
        if live.get("LineStatus") != "bost_Open":
            return STALE, (f"line {line['BaseLine']} of GRPO {grpo.get('DocNum')} was closed "
                           "after the scan — somebody else invoiced it")
        if "Quantity" in line:
            live_qty = float(live.get("RemainingOpenQuantity") or 0)
            if abs(live_qty - float(line["Quantity"])) > 1e-9:
                return STALE, (f"line {line['BaseLine']} now has {live_qty:g} open, not "
                               f"{float(line['Quantity']):g} — the money on the sheet is no "
                               "longer this document's money")

    res.attachment = str(grpo.get("AttachmentEntry") or "")
    scanned_attachment = str(entry.get("attachment_entry") or "")
    if scanned_attachment != res.attachment:
        if res.attachment:
            res.flags.append(f"the GRPO's attachment changed since the scan "
                             f"({scanned_attachment or 'none'} → {res.attachment}); "
                             "the live one is used")
        else:
            # Whatever the scan saw is gone. Patching the draft with it would
            # point at an attachment row the goods receipt no longer holds.
            res.flags.append(f"GRPO no longer carries a bill — attach in client "
                             f"(the scan saw Attachments2 {scanned_attachment})")

    # R6 — has anybody keyed this bill in the meantime
    #
    # Two questions, because one is not enough. The server can only match
    # NumAtCard exactly, so the variants are ASKED FOR by name; and everything
    # this vendor has open or posted in the window is compared with
    # rules.normalize_ref in Python, which is the only way `2633100542` finds
    # `.2633100542` — the pair that is live in Oil today.
    ref = res.ref or str(cells[COL["Y"]] or "").strip()
    for doc in ctx.posted_with_ref(ref):
        if doc.get("Cancelled") == "tNO":
            return STALE_DUPLICATE, (f"a posted A/P invoice now carries ref {ref!r}: DocEntry "
                                     f"{doc.get('DocEntry')} {doc.get('CardCode')} "
                                     f"{rules.inr(float(doc.get('DocTotal') or 0))}")
    for draft in ctx.open_drafts_with_ref(ref):
        if draft.get("Cancelled", "tNO") == "tNO":
            return STALE_DUPLICATE, (f"an open A/P draft now carries ref {ref!r}: DocEntry "
                                     f"{draft.get('DocEntry')} (user {draft.get('UserSign')})")

    since = rules.as_date(payload.get("DocDate") or grpo.get("DocDate")) - \
        dt.timedelta(days=DUP_WINDOW_DAYS)
    for doc in ctx.posted_for_vendor(payload["CardCode"], since=since):
        if doc.get("Cancelled") == "tNO" and rules.same_ref(doc.get("NumAtCard"), ref):
            return STALE_DUPLICATE, (
                f"a posted A/P invoice carries the same reference spelled "
                f"{str(doc.get('NumAtCard'))!r}: DocEntry {doc.get('DocEntry')} "
                f"{doc.get('CardCode')} {rules.inr(float(doc.get('DocTotal') or 0))}")

    for draft in ctx.open_drafts_for_vendor(payload["CardCode"]):
        if draft.get("Cancelled", "tNO") != "tNO":
            continue
        if rules.draft_targets_grpo(draft, docentry):
            return STALE_DUPLICATE, (f"an open A/P draft is already drawn from this GRPO: "
                                     f"DocEntry {draft.get('DocEntry')} ref "
                                     f"{draft.get('NumAtCard')!r} (user {draft.get('UserSign')})")
        if rules.same_ref(draft.get("NumAtCard"), ref):
            return STALE_DUPLICATE, (f"an open A/P draft carries the same reference spelled "
                                     f"{str(draft.get('NumAtCard'))!r}: DocEntry "
                                     f"{draft.get('DocEntry')} (user {draft.get('UserSign')})")

    # R7 — the vendor card
    vendor = ctx.vendor(payload["CardCode"])
    if not vendor:
        return STALE, f"vendor card {payload['CardCode']} could not be read"
    if vendor.get("Frozen") == "tYES":
        return STALE, f"vendor card {payload['CardCode']} has been FROZEN since the scan"
    if vendor.get("Valid") not in (None, "tYES"):
        return STALE, f"vendor card {payload['CardCode']} is no longer valid"
    return None


# --------------------------------------------------------------------------
# after the write
# --------------------------------------------------------------------------

def _record_created(res: RowResult, created: Any) -> bool:
    """CREATED, but only when SAP said WHICH document it made.

    `sapb1 draft` exiting 0 is not the same as SAP naming the draft. A 204 with
    no body, or a build that answers with something this code cannot read, used
    to become `CREATED` with `draft_entry: None` — a row that claims a document
    exists and cannot say which, so `--resume` skips it (it is not UNKNOWN), the
    attachment is patched onto `Drafts(None)`, and the operator is told to press
    Add on a draft nobody can find. That is an unknown outcome wearing the word
    CREATED, and it is handled as one: journalled, halted, gone and looked at.

    Returns True when the answer identified the draft.
    """
    entry = created.get("DocEntry") if isinstance(created, Mapping) else None
    try:
        res.draft_entry = int(entry)
    except (TypeError, ValueError):
        res.draft_entry = None
        return False
    if isinstance(created, Mapping):
        res.draft_num = created.get("DocNum")
    res.outcome = CREATED
    res.message = f"draft {res.draft_entry}"
    return True


def _attach_and_read_back(res: RowResult, entry: Mapping[str, Any], cells: Sequence[Any],
                          sap: SapCli, journal: store.Journal, run_stamp: str) -> None:
    """Point the draft at the vendor's bill, then read the draft back and report gaps.

    Neither step can lose the draft: it already exists. Anything that goes wrong
    from here is a flag on a document a person will open anyway.
    """
    # The LIVE value only. res.attachment is what the goods receipt held when it
    # was re-read seconds ago; falling back to the scan's value would patch the
    # draft with an Attachments2 row the GRPO no longer carries, while the flag
    # on the same row said the bill was gone. One of the two had to be wrong.
    attachment = res.attachment or None
    if attachment and res.draft_entry:
        try:
            sap.patch(f"Drafts({int(res.draft_entry)})",
                      {"AttachmentEntry": int(attachment)}, yes=True)
            journal.append({"event": "patch", "state": "done", "docentry": res.docentry,
                            "run": run_stamp, "draft_entry": res.draft_entry,
                            "attachment": int(attachment)})
        except SapError as e:
            res.flags.append(f"attachment not set on the draft ({str(e).splitlines()[0]}) — "
                             f"attach Attachments2 {attachment} in the client before Add")
            journal.append({"event": "patch", "state": "failed", "docentry": res.docentry,
                            "run": run_stamp, "draft_entry": res.draft_entry,
                            "message": str(e).splitlines()[0]})
    elif not attachment and not entry.get("attachment_entry"):
        res.flags.append("no bill attached to the GRPO — the draft points at nothing")
    # When the scan DID see one and the GRPO no longer holds it, _revalidate has
    # already said so ("GRPO no longer carries a bill — attach in client"); the
    # draft is left pointing at nothing rather than at a row that is gone.

    if not res.draft_entry:
        return
    try:
        draft = apreadback.read_draft(sap, int(res.draft_entry))
    except SapError as e:
        res.flags.append(f"could not read the draft back ({str(e).splitlines()[0]}) — "
                         "check it in Document Drafts")
        draft = None
    if draft:
        res.wtamount = draft.get("WTAmount")
        res.flags.extend(apreadback.readback_flags(
            draft, expect=entry.get("expect"),
            tds_choice=str(cells[COL["W"]]).strip().lower(),
            attachment_entry=attachment))
    if res.flags:
        res.outcome = CREATED_WITH_GAPS
        res.message = f"draft {res.draft_entry} · {len(res.flags)} thing(s) need a person"


# --------------------------------------------------------------------------
# resume
# --------------------------------------------------------------------------

def _resolve_unknown_row(res: RowResult, sidecar: store.Sidecar, ctx: _SendContext,
                         sap: SapCli, journal: store.Journal, run_stamp: str,
                         sending: bool) -> None:
    """Resolve one row whose write went out and never answered — by LOOKING, only.

    Nothing here sends a DRAFT. Either the draft this batch made is found (adopt
    it) or it is not (say so and leave the row alone forever). A batch never
    re-sends a row it does not understand; that is how one bill becomes two
    invoices.

    Finding a draft is not the same as finding OURS. Accounts keys these in the
    client all day, and the halt is exactly the window in which somebody does.
    So every candidate is put to rules.adoption_evidence, and one without
    evidence is reported as FOREIGN-DRAFT-FOUND and left completely alone — not
    adopted, not patched, not counted as this batch's work.

    The one write this can make is the attachment pointer on a draft it adopted,
    and only when the run was given --yes. `--resume` on its own is a look.
    """
    entry = sidecar.rows.get(str(res.docentry)) or {}
    payload = entry.get("payload") or {}
    card = payload.get("CardCode") or res.vendor
    ref = (entry.get("defaults") or {}).get("Y") or res.ref
    found: dict[Any, dict] = {}
    for draft in ctx.open_drafts_with_ref(str(ref or "")):
        if draft.get("Cancelled", "tNO") == "tNO":
            found[draft.get("DocEntry")] = draft
    for draft in ctx.open_drafts_for_vendor(card):
        if draft.get("Cancelled", "tNO") != "tNO":
            continue
        if rules.draft_targets_grpo(draft, res.docentry) or \
                rules.same_ref(draft.get("NumAtCard"), ref):
            found[draft.get("DocEntry")] = draft

    login_key = ctx.login_key() if found else None
    ours: dict[Any, tuple[dict, str]] = {}
    theirs: list[dict] = []
    for key, draft in found.items():
        why = rules.adoption_evidence(draft, batch_id=sidecar.batch_id, login_key=login_key,
                                      grpo_docentry=res.docentry)
        (ours.setdefault(key, (draft, why)) if why else theirs.append(draft))

    if len(ours) == 1:
        draft, why = next(iter(ours.values()))
        res.outcome = CREATED_RECOVERED
        res.draft_entry = draft.get("DocEntry")
        res.draft_num = draft.get("DocNum")
        res.message = (f"the draft the unknown outcome left behind is {res.draft_entry} "
                       f"— adopted, not re-sent ({why})")
        journal.append({"event": "resume", "state": "recovered", "docentry": res.docentry,
                        "run": run_stamp, "draft_entry": res.draft_entry, "evidence": why})
        sidecar.update_outcome(res.docentry, {"state": CREATED_RECOVERED,
                                              "draft_entry": res.draft_entry,
                                              "draft_num": res.draft_num, "run": run_stamp})
        if not draft.get("AttachmentEntry") and entry.get("attachment_entry"):
            res.attachment = str(entry["attachment_entry"])
            if sending:
                _patch_attachment_only(res, sap, journal, run_stamp)
            else:
                # Adopting the draft is a READ. Patching it is a write, and
                # this run was never given permission to make one.
                res.flags.append(f"the recovered draft has no attachment; re-run with --yes "
                                 f"to point it at Attachments2 {res.attachment}")
        res.flags.extend(apreadback.readback_flags(
            draft, expect=entry.get("expect"),
            tds_choice=((entry.get("tds") or {}).get("choice")),
            attachment_entry=entry.get("attachment_entry")))
    elif len(ours) > 1:
        res.outcome = UNKNOWN_UNRESOLVED
        res.message = (f"{len(ours)} open drafts match this row ({sorted(ours)}) — a "
                       "person has to decide which is real and remove the others in the "
                       "SAP client")
        journal.append({"event": "resume", "state": "several", "docentry": res.docentry,
                        "run": run_stamp, "drafts": sorted(ours)})
    elif theirs:
        res.outcome = FOREIGN_DRAFT_FOUND
        res.message = (
            "this bill is already drafted, and NOT by this batch: "
            + "; ".join(rules.foreign_draft_reason(d) for d in theirs[:3])
            + ". Nothing was adopted, patched or re-sent. Open it in Document Drafts: if it is "
              "the one this batch made, finish it there; if it is somebody else's, this row is "
              "already done and there is nothing to send.")
        journal.append({"event": "resume", "state": "foreign", "docentry": res.docentry,
                        "run": run_stamp,
                        "drafts": sorted(d.get("DocEntry") for d in theirs)})
    else:
        res.outcome = UNKNOWN_UNRESOLVED
        res.message = ("looked for the draft by GRPO and by vendor reference and found "
                       "nothing. It was NOT re-sent. Check Document Drafts yourself, and "
                       "if it really is not there, re-scan and draft this bill again.")
        journal.append({"event": "resume", "state": "unresolved", "docentry": res.docentry,
                        "run": run_stamp})


def _patch_attachment_only(res: RowResult, sap: SapCli, journal: store.Journal,
                           run_stamp: str) -> None:
    try:
        sap.patch(f"Drafts({int(res.draft_entry)})",
                  {"AttachmentEntry": int(res.attachment)}, yes=True)
        journal.append({"event": "patch", "state": "done", "docentry": res.docentry,
                        "run": run_stamp, "draft_entry": res.draft_entry})
    except SapError as e:
        res.flags.append(f"attachment not set on the recovered draft ({str(e).splitlines()[0]})")


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

def _write_dryrun(path: Path, docentry: Any, payload: Mapping[str, Any], preview: Any) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(f"\n===== GRPO DocEntry {docentry} =====\n")
        fh.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
        if preview is not None:
            fh.write("-- sapb1 --dry-run said --\n")
            fh.write(json.dumps(preview, indent=2, ensure_ascii=False) + "\n")


def _say_row(say, res: RowResult) -> None:
    head = f"   row {res.row:>3} · GRPO {res.docnum} · {res.vendor_name[:28]:<28}"
    money = rules.inr(res.gross) if res.gross else ""
    say(f"{head} {money:>16}  {res.outcome}")
    if res.message:
        say(f"        {res.message}")
    for flag in res.flags:
        say(f"        ⚠ {flag}")


def _summarize(results: Sequence[RowResult]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for r in results:
        counts[r.outcome] = counts.get(r.outcome, 0) + 1
    return counts


RESULT_HEADERS = ["Row", "GRPO DocNum", "GRPO DocEntry", "Vendor", "Vendor name", "Ref", "Gross",
                  "Outcome", "Draft DocEntry", "Draft DocNum", "Attachment", "TDS on draft",
                  "Readback flags", "Message"]
RESULT_WIDTHS = [5, 14, 13, 13, 30, 22, 14, 20, 14, 14, 12, 12, 60, 70]


def _write_results(out_dir: Path, batch_id: str, run_stamp: str,
                   results: Sequence[RowResult]) -> Path:
    rows = [[r.row, r.docnum, r.docentry, r.vendor, r.vendor_name, r.ref, r.gross, r.outcome,
             r.draft_entry or "", r.draft_num or "", r.attachment or "", r.wtamount if
             r.wtamount != "" else "", " · ".join(r.flags), r.message]
            for r in results]
    rows = [[xlsx.clean_text(v) for v in row] for row in rows]
    path = out_dir / f"results-{batch_id}-{run_stamp}.xlsx"
    xlsx.write_workbook(path, [xlsx.SheetSpec(name="Results", headers=RESULT_HEADERS, rows=rows,
                                              widths=RESULT_WIDTHS,
                                              styles={6: "inr", 11: "inr"})])
    return path


def _report(say, results, summary, sidecar, sap, book, sending, halted) -> None:
    say("")
    for outcome, n in sorted(summary.items()):
        say(f"   {outcome:<20} {n:>4}")
    made = [r for r in results if r.outcome in MADE_A_DRAFT]
    say("")
    if halted:
        say("   THE RUN STOPPED — the reason is on stderr, above. Nothing else was attempted.")
    if made:
        say(f"   {len(made)} draft(s) created under login {sap.user}. Nothing is posted: open")
        say("   SAP B1 → Purchasing A/P → Purchasing Reports → Document Drafts Report,")
        say(f"   tick A/P Invoice + Open Only, User = {sap.user}, and press Add on each one.")
        say(f"   They all carry {sidecar.batch_id} in Remarks, so you can search on it.")
    elif not sending:
        say("   Nothing was sent. Re-run with --yes when the preview is what you want.")
    say(f"   results   {book}")
    say(f"   audit     grep {sidecar.batch_id} queries/*/sap-writes.jsonl")


# --------------------------------------------------------------------------
# stand-alone entry point (acc.py normally calls run_send)
# --------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="acc batch send", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workbook")
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--max-age-days", type=int, default=3)
    ap.add_argument("--env")
    ap.add_argument("--quiet", action="store_true")
    return ap


def main(argv: list[str] | None = None) -> int:
    return run_send(build_parser().parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
