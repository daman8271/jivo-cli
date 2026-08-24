"""SapCli — every SAP call this toolkit makes, funnelled through `sapb1`.

Why a subprocess and not the Service Layer directly: the properties Accounts is
trusting live in the Go CLI, not in the HTTP call. It refuses a write without
`--yes` when nobody is at a terminal, it logs an intent/outcome pair for every
attempt to the shared write log, and it draws the line between "SAP said no,
nothing committed" (exit 6) and "the request went out and no answer came back,
go look" (exit 7). A Python re-implementation would fork all of that.

The cost is a process spawn per call (1-3 s over the home bridge), which is paid
back by asking fewer, bigger questions — see context.ScanContext.

Exit codes, as the CLI defines them in internal/cli/exitcode.go:

    0  fine                       (no exception)
    2  usage                      SapUsage
    3  config                     SapConfig
    4  auth                       SapAuth
    5  network                    SapUnreachable
    6  SAP answered with an error SapRejected          nothing committed
    7  write outcome unknown      SapUnknownOutcome    may have committed — go look
    8  write done, read-back bad  SapVerifyFailed      SAP already answered, go look
    9  a guard said no           SapRefused           spelled right, answer still no

Only SapUnreachable is retried, and only for reads. A write is never retried:
re-sending a draft whose answer was lost is exactly how you get two of them.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

# Windows consoles default to cp1252 and die on the rupee sign and the arrows
# this toolkit prints. Same guard as harness/bin/setup.py.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


class SapError(RuntimeError):
    """Anything sapb1 refused to do. `code` is its exit code."""

    def __init__(self, message: str, code: int | None = None,
                 stdout: str = "", stderr: str = "", argv: Sequence[str] = ()) -> None:
        super().__init__(message)
        self.code = code
        self.stdout = stdout
        self.stderr = stderr
        self.argv = list(argv)


class SapUsage(SapError):
    """Exit 2 — the command line or the payload was wrong. Nothing was sent."""


class SapConfig(SapError):
    """Exit 3 — host/company/credentials not configured. Nothing was sent."""


class SapAuth(SapError):
    """Exit 4 — SAP would not log us in."""


class SapUnreachable(SapError):
    """Exit 5 — could not reach the Service Layer at all. Retryable."""


class SapRejected(SapError):
    """Exit 6 — SAP answered with an error envelope. NOTHING was committed."""


class SapUnknownOutcome(SapError):
    """Exit 7 — the write was sent and no answer came back.

    Never replay it. Query SAP for what exists and tell the operator.
    """


class SapVerifyFailed(SapError):
    """Exit 8 — SAP answered the write but the read-back after it disagreed."""


class SapRefused(SapError):
    """Exit 9 — a guard in the CLI said no. The command was fine; the answer is no."""


class SapWriteRefused(SapError):
    """This SapCli was built read-only and was asked to write.

    Not a SAP condition — a local guard. `acc batch scan` runs behind it, so a
    scan cannot write even if a future edit tried to.
    """


# Exit code -> exception. 0 is success, so it maps to None rather than to a
# class: there is no "SapOK" to raise.
EXIT_EXCEPTIONS: dict[int, type[SapError] | None] = {
    0: None,
    2: SapUsage,
    3: SapConfig,
    4: SapAuth,
    5: SapUnreachable,
    6: SapRejected,
    7: SapUnknownOutcome,
    8: SapVerifyFailed,
    9: SapRefused,
}

# Waits between read retries, in seconds.
RETRY_BACKOFF = (2, 4, 8)

# How long one sapb1 call may take before we stop waiting on it. The CLI has its
# own SAPB1_TIMEOUT per HTTP request; this is the outer limit on the PROCESS,
# because a spawn that never returns hangs the batch with no message at all.
# Generous on purpose: the open-A/P-draft sweep measured 90 s on Oil, and a
# bridged --all over a slow link is minutes.
SUBPROC_TIMEOUT = 600

# Exit codes that mean the request never left the CLI. Everything else that is
# not 0 is treated, on a write, as "we do not know" — see _write.
NOTHING_WAS_SENT = frozenset({2, 3, 5, 6})

BRIDGE_HINT = (
    "From outside the office IP: bash connections/sap-home-bridge.sh, then export "
    "SAPB1_HOST=127.0.0.1 SAPB1_PORT=15000 SAPB1_TIMEOUT=180."
)


def find_repo(start: Path | None = None) -> Path:
    """Walk up from `start` (this file by default) to the jivo-cli checkout."""
    here = (start or Path(__file__)).resolve()
    for p in [here] + list(here.parents):
        if (p / "sap-b1" / "cli").is_dir() or (p / "sap-b1" / "accounts-kit").is_dir():
            return p
    raise SapConfig(f"cannot find jivo-cli/sap-b1 above {here}")


def resolve_cli(repo: Path, windows: bool | None = None) -> Path:
    """The sapb1 binary for this platform.

    Operator boxes are Windows and run the prebuilt exe out of accounts-kit;
    Mac/Linux run the Go binary in sap-b1/cli. Either one is accepted on either
    platform when the native one is missing, so a Mac checkout that only has the
    exe still resolves rather than failing with "not configured".
    """
    if windows is None:
        windows = os.name == "nt"
    exe = repo / "sap-b1" / "accounts-kit" / "sapb1.exe"
    posix = repo / "sap-b1" / "cli" / "sapb1"
    first, second = (exe, posix) if windows else (posix, exe)
    if first.exists():
        return first
    if second.exists():
        return second
    return first


def read_env_file(path: Path | str) -> dict[str, str]:
    """KEY=value lines, comments and blanks skipped. Missing file -> {}."""
    out: dict[str, str] = {}
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    out[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return out


class SapCli:
    """A configured `sapb1`.

    allow_writes=False (the default) makes draft() and patch() raise before a
    process is spawned. `acc batch scan` uses that; only `acc batch send` builds
    a writable one.
    """

    def __init__(
        self,
        repo: Path | str | None = None,
        company: str | None = None,
        env_file: Path | str | None = None,
        allow_writes: bool = False,
        timeout: int | None = None,
        retries: int = len(RETRY_BACKOFF),
        sleep: Callable[[float], None] = time.sleep,
        windows: bool | None = None,
    ) -> None:
        self.repo = Path(repo).resolve() if repo else find_repo()
        self.cli = resolve_cli(self.repo, windows)
        if not self.cli.exists():
            raise SapConfig(
                f"sapb1 not found at {self.cli} — is this a jivo-cli checkout? "
                "(Windows kits run sap-b1\\accounts-kit\\sapb1.exe)"
            )
        self.company = company
        self.allow_writes = allow_writes
        self.retries = retries
        self._sleep = sleep

        # --env picks the LOGIN (whose name the drafts land under); it must not
        # override an exported SAPB1_HOST/PORT, because that is the bridge and
        # the file still carries the office address. Same precedence the skill's
        # precheck.py uses, but applied to a private copy of the environment so
        # a password from an operator env file never lands in this process.
        env = dict(os.environ)
        self.env_path: Path | None = None
        if env_file:
            path = Path(env_file)
            if not path.is_absolute():
                path = self.cli.parent / path
            if not path.exists():
                # An --env the operator typed and that is not there is never
                # "carry on with the default login": the drafts would land under
                # somebody else's name, which is exactly what --env exists to
                # decide. Name the path so the typo is visible.
                raise SapConfig(
                    f"--env {env_file}: no such file — looked in {path}. "
                    f"Operator env files live next to sapb1 ({self.cli.parent}); "
                    "run `ls` there to see which names exist.")
            self.env_path = path
            file_env = read_env_file(path)
            # os.environ wins for everything EXCEPT the login. An exported
            # SAPB1_USER left over from an earlier session would silently send
            # this operator's drafts under somebody else's name while the banner
            # and the About sheet both said --env had been honoured. Name both
            # and stop rather than guess which one they meant.
            shell_user = os.environ.get("SAPB1_USER")
            file_user = file_env.get("SAPB1_USER")
            if shell_user and file_user and shell_user != file_user:
                raise SapConfig(
                    f"SAPB1_USER is exported in this shell as {shell_user!r} but --env {path.name} "
                    f"says {file_user!r} — the drafts would land under {shell_user!r}. "
                    "`unset SAPB1_USER` (or drop --env) and run it again.")
            for k, v in file_env.items():
                env.setdefault(k, v)
        env.setdefault("SAPB1_TIMEOUT", str(timeout or 180))
        if timeout:
            env["SAPB1_TIMEOUT"] = str(timeout)
        self.env = env
        self.env_file = str(env_file) if env_file else None
        try:
            self.subproc_timeout = int(env.get("SAPB1_SUBPROC_TIMEOUT") or SUBPROC_TIMEOUT)
        except ValueError:
            self.subproc_timeout = SUBPROC_TIMEOUT

    # -- identity, for the About sheet and the console banner ------------

    @property
    def user(self) -> str:
        return self.env.get("SAPB1_USER") or self._dotenv().get("SAPB1_USER") or "?"

    @property
    def company_db(self) -> str:
        return self.company or self.default_company_db

    @property
    def default_company_db(self) -> str:
        """The company this environment would use if nobody named one.

        Kept apart from company_db because `acc batch send` names the company
        itself (the sidecar's, so the drafts cannot land in another company's
        books) — which also makes company_db always agree with the sidecar and
        the mismatch invisible. This is the value that can actually disagree,
        and the operator is told when it does.
        """
        return (self.env.get("SAPB1_COMPANYDB") or self._dotenv().get("SAPB1_COMPANYDB")
                or "JIVO_OIL_HANADB")

    @property
    def route(self) -> str:
        host = self.env.get("SAPB1_HOST") or self._dotenv().get("SAPB1_HOST") or "?"
        port = self.env.get("SAPB1_PORT") or self._dotenv().get("SAPB1_PORT") or "50000"
        return f"{host}:{port}"

    def _dotenv(self) -> dict[str, str]:
        if not hasattr(self, "_dotenv_cache"):
            self._dotenv_cache = read_env_file(self.cli.parent / ".env")
        return self._dotenv_cache

    # -- reads -----------------------------------------------------------

    def query(
        self,
        entity: str,
        filter: str | None = None,
        select: str | None = None,
        orderby: str | None = None,
        top: int | None = None,
        all: bool = False,
        page_size: int | None = None,
        company: str | None = None,
        retries: int | None = None,
    ) -> list[dict]:
        if all and top:
            # --all sweeps every page and the CLI ignores --top while it does,
            # so asking for both silently returns more rows than the caller
            # bounded. A scan that thinks it read 3 vendors and read 300 is a
            # wrong answer, not a slow one.
            raise SapUsage(f"{entity}: all=True and top={top} together — --all ignores --top; "
                           "ask for one or the other")
        argv = ["query", entity, "--json"]
        if filter:
            argv += ["--filter", filter]
        if select:
            argv += ["--select", select]
        if orderby:
            argv += ["--orderby", orderby]
        if all:
            argv.append("--all")
            if page_size:
                argv += ["--page-size", str(page_size)]
        else:
            if top:
                argv += ["--top", str(top)]
            if page_size:
                argv += ["--page-size", str(page_size)]
        out = self._run(argv, company=company, retry=True,
                        retries=self.retries if retries is None else retries)
        return self._json(out or "[]", argv, what=f"reading {entity}")

    @staticmethod
    def _json(text: str, argv: Sequence[str], what: str) -> Any:
        """Parse what sapb1 printed, or say what it printed instead.

        A build that prints a warning, a Go panic or an HTML error page on stdout
        and still exits 0 used to come back as a JSONDecodeError with the offset
        and nothing else — unreadable to an operator and indistinguishable from a
        bug in this file. The first 200 characters are what tells them which.
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise SapError(
                f"sapb1 exited 0 while {what} but did not print JSON: "
                f"{text.strip()[:200]!r} ({e})", code=0, stdout=text, argv=argv) from e

    def query_all(self, entity: str, **kw: Any) -> list[dict]:
        kw["all"] = True
        return self.query(entity, **kw)

    # -- writes ----------------------------------------------------------

    def draft(
        self,
        doctype: str,
        payload: Mapping[str, Any] | None = None,
        data_file: Path | str | None = None,
        dry_run: bool = False,
        yes: bool = False,
        company: str | None = None,
    ) -> Any:
        """`sapb1 draft <doctype>`. Returns SAP's created object (or the dry-run JSON)."""
        self._require_writes("draft " + doctype)
        argv = ["draft", doctype, "--json"]
        return self._write(argv, payload, data_file, dry_run, yes, company)

    def patch(
        self,
        target: str,
        payload: Mapping[str, Any] | None = None,
        data_file: Path | str | None = None,
        dry_run: bool = False,
        yes: bool = False,
        company: str | None = None,
    ) -> Any:
        """`sapb1 patch "<Entity(key)>"`. Live immediately; the CLI cannot undo it."""
        self._require_writes("patch " + target)
        argv = ["patch", target, "--json"]
        return self._write(argv, payload, data_file, dry_run, yes, company)

    def _require_writes(self, what: str) -> None:
        if not self.allow_writes:
            raise SapWriteRefused(
                f"this SapCli is read-only and was asked to {what} — "
                "scan never writes; only `acc batch send` builds a writable client"
            )

    def _write(self, argv, payload, data_file, dry_run, yes, company):
        if not dry_run and not yes:
            raise SapUsage(
                "refusing to write without --yes or --dry-run: sapb1 would refuse it too "
                "(stdin is not a terminal here, so nobody can answer the prompt)"
            )
        tmp = None
        try:
            if data_file is None:
                if payload is None:
                    raise SapUsage("no payload given to write")
                fd, name = tempfile.mkstemp(prefix="apbatch-", suffix=".json")
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(payload, fh, indent=2)
                tmp = data_file = name
            argv = list(argv) + ["--data-file", str(data_file)]
            if dry_run:
                argv.append("--dry-run")
                out = self._run(argv, company=company, retry=False, retries=0)
                # A dry run commits nothing, so unreadable output here is a
                # refusal to preview, not a document that may exist.
                return self._json(out, argv, what="previewing the write") if out.strip() else None
            argv.append("--yes")
            out = self._send(argv, company)
            if not out.strip():
                return None
            try:
                return json.loads(out)
            except json.JSONDecodeError as e:
                # Exit 0 and nothing this build can read. The write went out and
                # the answer is unreadable, which is the exit-7 shape arrived at
                # from the other side: never "nothing happened".
                raise SapUnknownOutcome(
                    "sapb1 exited 0 after SENDING but did not print JSON: "
                    f"{out.strip()[:200]!r} — the document may exist. Do not re-run it: "
                    "look in Document Drafts, then `acc batch send --resume`.",
                    code=0, stdout=out, argv=argv) from e
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    def _send(self, argv: Sequence[str], company: str | None) -> str:
        """A real write. Anything but a clean 0 or a known "nothing was sent".

        The CLI's exit codes are a promise about whether the request reached SAP.
        2/3/5/6 are made BEFORE or INSTEAD of the POST — bad usage, no config, no
        connection, SAP answered with an error envelope — and after any of them
        nothing exists. Every other non-zero code is a code this build does not
        have that promise for: 8 (SAP answered, read-back disagreed), a signal
        (negative, e.g. -15 when something killed it mid-flight), a future exit
        code, or a plain 1 from a panic.

        Guessing "nothing happened" there is the one guess that creates a second
        A/P invoice. So they all become SapUnknownOutcome: the batch halts, the
        row is journalled unknown, and a person looks in Document Drafts. A false
        "go look" costs a minute; a false "nothing happened" costs a duplicate
        posting.
        """
        try:
            return self._run(argv, company=company, retry=False, retries=0, write=True)
        except SapError as e:
            if e.code == 0 or e.code in NOTHING_WAS_SENT or isinstance(e, SapUnknownOutcome):
                raise
            raise SapUnknownOutcome(
                f"sapb1 exited {e.code}, which this build cannot read as "
                f"'nothing was sent' — treat it as UNKNOWN and go look in SAP before "
                f"anything is re-sent.\n  {e}",
                code=e.code, stdout=e.stdout, stderr=e.stderr, argv=e.argv) from e

    # -- the actual spawn ------------------------------------------------

    def _run(self, argv: Sequence[str], company: str | None, retry: bool, retries: int,
             write: bool = False) -> str:
        cmd = [str(self.cli)] + list(argv)
        c = company or self.company
        if c:
            cmd += ["--company", c]

        attempt = 0
        while True:
            try:
                r = subprocess.run(cmd, cwd=str(self.cli.parent), env=self.env,
                                   capture_output=True, text=True,
                                   timeout=self.subproc_timeout)
            except OSError as e:                       # binary vanished / not executable
                raise SapConfig(f"cannot run {self.cli}: {e}", argv=cmd) from e
            except subprocess.TimeoutExpired as e:
                # A read that never came back was never an answer: retryable.
                # A WRITE that never came back may be sitting in SAP — the exit-7
                # shape, arrived at from this side.
                if write:
                    raise SapUnknownOutcome(
                        f"sapb1 did not return within {self.subproc_timeout}s and it was "
                        "SENDING — the document may exist. Do not re-run it: look in "
                        "Document Drafts, then `acc batch send --resume`.", code=None,
                        argv=cmd) from e
                exc = SapUnreachable(
                    f"sapb1 did not return within {self.subproc_timeout}s\n  {BRIDGE_HINT}",
                    code=None, argv=cmd)
                if retry and attempt < retries:
                    self._sleep(RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)])
                    attempt += 1
                    continue
                raise exc from e
            if r.returncode == 0:
                return r.stdout
            exc = self._exception_for(r, cmd)
            if retry and isinstance(exc, SapUnreachable) and attempt < retries:
                self._sleep(RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)])
                attempt += 1
                continue
            raise exc

    @staticmethod
    def _exception_for(r: subprocess.CompletedProcess, cmd: Sequence[str]) -> SapError:
        detail = (r.stderr or "").strip().splitlines()
        msg = detail[-1] if detail else f"sapb1 exited {r.returncode}"
        cls = EXIT_EXCEPTIONS.get(r.returncode) or SapError
        if cls is SapUnreachable:
            msg = f"{msg}\n  {BRIDGE_HINT}"
        return cls(msg, code=r.returncode, stdout=r.stdout or "",
                   stderr=r.stderr or "", argv=cmd)


def chunked(items: Iterable[Any], size: int) -> list[list[Any]]:
    """Split a list into `size`-long chunks — OData filters get long fast."""
    out: list[list[Any]] = []
    batch: list[Any] = []
    for it in items:
        batch.append(it)
        if len(batch) == size:
            out.append(batch)
            batch = []
    if batch:
        out.append(batch)
    return out


def odata_str(value: str) -> str:
    """A single-quoted OData literal, with quotes doubled the way OData wants."""
    return "'" + str(value).replace("'", "''") + "'"


def or_filter(field: str, values: Sequence[str], numeric: bool = False) -> str:
    """`Field eq 'a' or Field eq 'b'` — the poor man's IN()."""
    if numeric:
        return " or ".join(f"{field} eq {int(v)}" for v in values)
    return " or ".join(f"{field} eq {odata_str(v)}" for v in values)


class FakeSap:
    """A SapCli-shaped stand-in for tests. Contacts nothing, remembers everything.

    `tables` maps an entity name to either a list of rows or a callable
    (filter, select, **kw) -> rows, so a test can be as dumb or as scripted as it
    needs. Every call is recorded; `writes` stays empty unless something tried to
    write, which is how the scan's read-only guarantee is asserted.
    """

    def __init__(self, tables: Mapping[str, Any] | None = None,
                 company: str = "JIVO_OIL_HANADB", allow_writes: bool = False,
                 user: str = "USER36", route: str = "fake:0",
                 fail: Mapping[str, SapError] | None = None) -> None:
        self.tables = dict(tables or {})
        self.company = company
        self.company_db = company
        self.default_company_db = company
        self.allow_writes = allow_writes
        self.user = user
        self.route = route
        self.env_file = None
        self.env_path = None
        self.calls: list[dict] = []
        self.writes: list[dict] = []
        self.fail = dict(fail or {})
        self.draft_result: Any = {"DocEntry": 90001, "DocNum": 626089001}
        # One scripted answer per REAL draft (never per dry run): a dict to
        # return or an exception to raise. Left empty, every draft answers with
        # draft_result. This is how a test says "row 2 gets exit 7".
        self.draft_results: list[Any] = []

    # -- reads -----------------------------------------------------------

    def query(self, entity: str, filter: str | None = None, select: str | None = None,
              orderby: str | None = None, top: int | None = None, all: bool = False,
              page_size: int | None = None, company: str | None = None,
              retries: int | None = None) -> list[dict]:
        if all and top:
            raise SapUsage(f"{entity}: all=True and top={top} together — --all ignores --top")
        self.calls.append({"entity": entity, "filter": filter, "select": select,
                           "orderby": orderby, "top": top, "all": all,
                           "company": company or self.company})
        if entity in self.fail:
            raise self.fail[entity]
        table = self.tables.get(entity, [])
        # `all` and `page_size` are handed to a scripted table on purpose: the
        # Service Layer answers a capped question differently from a swept one
        # (20 rows by default, every row with --all), and a fake that cannot tell
        # the two apart cannot reproduce the bug where a 25th open draft was the
        # duplicate nobody saw.
        rows = (table(filter, select, orderby=orderby, top=top, all=all, page_size=page_size)
                if callable(table) else list(table))
        rows = [dict(r) for r in rows]
        return rows[:top] if top else rows

    def query_all(self, entity: str, **kw: Any) -> list[dict]:
        kw["all"] = True
        return self.query(entity, **kw)

    # -- writes ----------------------------------------------------------

    def draft(self, doctype: str, payload=None, data_file=None, dry_run: bool = False,
              yes: bool = False, company: str | None = None):
        if not self.allow_writes:
            raise SapWriteRefused(f"read-only FakeSap was asked to draft {doctype}")
        self._require_yes_or_dry_run(dry_run, yes)
        self.writes.append({"kind": "draft", "doctype": doctype, "payload": payload,
                            "data_file": str(data_file) if data_file else None,
                            "dry_run": dry_run, "yes": yes})
        if dry_run:
            return {"dryRun": True}
        result = self.draft_results.pop(0) if self.draft_results else self.draft_result
        if isinstance(result, Exception):
            raise result
        return result

    def patch(self, target: str, payload=None, data_file=None, dry_run: bool = False,
              yes: bool = False, company: str | None = None):
        if not self.allow_writes:
            raise SapWriteRefused(f"read-only FakeSap was asked to patch {target}")
        self._require_yes_or_dry_run(dry_run, yes)
        self.writes.append({"kind": "patch", "target": target, "payload": payload,
                            "dry_run": dry_run, "yes": yes})
        return None

    @staticmethod
    def _require_yes_or_dry_run(dry_run: bool, yes: bool) -> None:
        """The real client's precondition, enforced here too.

        A fake that accepts a write the real one would refuse turns "no test ever
        caught it" into "the code path was never really exercised".
        """
        if not dry_run and not yes:
            raise SapUsage(
                "refusing to write without --yes or --dry-run: sapb1 would refuse it too "
                "(stdin is not a terminal here, so nobody can answer the prompt)")

    # -- assertions helpers ----------------------------------------------

    def entities_called(self) -> list[str]:
        return [c["entity"] for c in self.calls]
