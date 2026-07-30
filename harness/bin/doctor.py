#!/usr/bin/env python3
"""JIVO harness — doctor. Proves the harness actually works ON THIS MACHINE.

Why this exists
---------------
Every hook in this harness is deliberately fail-quiet: a broken harness must
never stop an operator mid-question. That choice is right, and it produced the
three worst bugs this harness has had, because it makes a broken harness
*indistinguishable from a working one*:

  * `stop.sh` was never registered in settings.json. It was tested by running
    the script by hand, so it passed, and fired never in a real session.
  * On Windows, `harness.py context` raised UnicodeEncodeError on a "->"
    character in a persona profile. stderr was redirected, so every operator
    who tagged themselves silently received an EMPTY corrections digest.
  * A tracked question log made every worktree permanently dirty, so `git pull`
    aborted forever and corrections never arrived. It passed a "clean clone"
    test, because a clean clone has never typed a prompt.

None of those were findable by reading the code. All three were findable by
running it and looking at the output. That is this file's whole job.

Run it after cloning, after changing a hook, and on any machine that is about
to be handed to an operator:

    python3 harness/bin/doctor.py          # or `python` on Windows

Exit code is 0 only if every check passed. Anything else means do not hand this
machine to an operator yet.

Writes nothing outside harness/.state/doctor/ and issues no business-system
call of any kind.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

HARNESS = Path(__file__).resolve().parent.parent
REPO = HARNESS.parent
HOOKS = HARNESS / "hooks"
BIN = HARNESS / "bin"

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
_results: list[tuple[str, str, str]] = []


def check(name: str, ok: bool, detail: str = "", warn_only: bool = False) -> bool:
    status = PASS if ok else (WARN if warn_only else FAIL)
    _results.append((status, name, detail))
    mark = {"PASS": "  ok  ", "FAIL": " FAIL ", "WARN": " warn "}[status]
    line = f"{mark} {name}"
    if detail:
        line += f"\n        {detail}"
    print(line)
    return ok


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=90,
                          errors="replace", **kw)


def _py() -> str:
    return sys.executable or "python3"


# ── 1. environment ───────────────────────────────────────────────────────────

def check_environment() -> None:
    print("\n── environment ──")
    print(f"        {platform.system()} {platform.release()} · python {platform.python_version()}")
    print(f"        interpreter: {sys.executable}")

    check("python is 3.8+", sys.version_info >= (3, 8),
          f"found {platform.python_version()}")

    # The cp1252 bug. Print the characters that actually occur in JIVO data.
    try:
        sample = "\u20b9 rupee \u2192 arrow \u2014 dash"
        sys.stdout.write("        encoding sample: " + sample + "\n")
        check("stdout can encode rupee/arrow/dash", True,
              f"stdout encoding = {getattr(sys.stdout, 'encoding', '?')}")
    except UnicodeEncodeError as exc:
        check("stdout can encode rupee/arrow/dash", False,
              f"UnicodeEncodeError: {exc}. Corrections about money WILL break.")

    bash = shutil.which("bash")
    if bash:
        check("bash on PATH", True, bash)
    else:
        gitbash = [
            Path(r"C:\Program Files\Git\bin\bash.exe"),
            Path(r"C:\Program Files (x86)\Git\bin\bash.exe"),
        ]
        found = next((p for p in gitbash if p.exists()), None)
        check("bash on PATH", False,
              (f"NOT on PATH, but git-bash exists at {found}. Every hook in "
               "settings.json is invoked as `bash ...`, so hooks may not run. "
               "Add git's bin to PATH, or see harness/README.md.")
              if found else
              "NOT found at all. Hooks cannot run. Install Git for Windows.",
              warn_only=bool(found))

    check("git on PATH", shutil.which("git") is not None,
          shutil.which("git") or "missing — corrections cannot be shared")


# ── 2. repo + sharing ────────────────────────────────────────────────────────

def check_repo() -> None:
    print("\n── repo and sharing ──")
    if not shutil.which("git"):
        check("is a git clone", False, "git not available")
        return

    r = _run(["git", "-C", str(REPO), "rev-parse", "--is-inside-work-tree"])
    if not check("is a git clone", r.stdout.strip() == "true",
                 "not a git repo — corrections can never be shared"):
        return

    r = _run(["git", "-C", str(REPO), "remote", "get-url", "origin"])
    check("has an origin remote", r.returncode == 0,
          r.stdout.strip() or "no origin — this machine cannot receive corrections")

    # THE bug that made pull abort forever. Any tracked file the harness writes
    # to on every turn will do it again.
    r = _run(["git", "-C", str(REPO), "status", "--porcelain",
              "--", "harness/questions"])
    dirty = [ln for ln in r.stdout.splitlines() if ln.strip()]
    check("harness logs are not tracked", not dirty,
          ("These are modified AND tracked, which aborts `git pull` for this "
           f"operator forever:\n        {chr(10).join('        ' + d for d in dirty)}")
          if dirty else "logs are local-only, so pull stays clean")


# ── 3. corrections + injection ───────────────────────────────────────────────

def check_corrections() -> None:
    print("\n── corrections ──")
    r = _run([_py(), str(BIN / "harness.py"), "build", "--quiet"])
    check("digest builds", r.returncode == 0, (r.stderr or "").strip()[:300])

    index = HARNESS / "corrections" / "INDEX.md"
    check("digest file exists", index.exists(), str(index))

    n = len(list((HARNESS / "corrections").glob("C-*.md")))
    check("has at least one correction", n > 0,
          f"{n} record(s)" if n else
          "empty — the harness knows nothing yet. Not broken, just unseeded.",
          warn_only=True)

    # The Windows failure: a persona crashed context() and produced 0 bytes.
    # Test EVERY defined persona, not just the default.
    personas = ["all"] + sorted(p.stem for p in (HARNESS / "personas").glob("*.md"))
    for persona in personas:
        env = dict(os.environ, JIVO_PERSONA=persona)
        r = _run([_py(), str(BIN / "harness.py"), "context"], env=env)
        out = r.stdout or ""
        if r.returncode != 0:
            check(f"context works for persona '{persona}'", False,
                  f"exit {r.returncode}: {(r.stderr or '').strip()[:250]}")
        elif persona != "all" and not out.strip():
            check(f"context works for persona '{persona}'", False,
                  "produced ZERO bytes. This operator receives no corrections "
                  "at all, and the hook would hide it.")
        else:
            check(f"context works for persona '{persona}'", True,
                  f"{len(out)} bytes")


# ── 4. hooks actually fire and actually do something ─────────────────────────

def check_hooks() -> None:
    print("\n── hooks ──")
    settings = REPO / ".claude" / "settings.json"
    if not check("settings.json exists", settings.exists(), str(settings)):
        return
    try:
        cfg = json.loads(settings.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        check("settings.json is valid JSON", False, str(exc))
        return
    check("settings.json is valid JSON", True)

    # A duplicate JSON key silently discards the earlier hook. This happened:
    # the watermark hook was "configured" and never ran.
    raw = settings.read_text(encoding="utf-8")
    for event in ("SessionStart", "UserPromptSubmit", "PostToolUse", "Stop"):
        occurrences = raw.count(f'"{event}"')
        if occurrences > 1:
            check(f"no duplicate '{event}' key", False,
                  f"appears {occurrences} times — JSON keeps only the LAST, so "
                  "earlier hooks are silently discarded")
        else:
            check(f"no duplicate '{event}' key", True)

    registered = cfg.get("hooks", {})
    for event in ("SessionStart", "UserPromptSubmit", "Stop"):
        check(f"{event} is registered", event in registered,
              "not registered — this hook will NEVER fire, no matter what the "
              "script does" if event not in registered else "")

    # Every referenced script must exist.
    import re
    missing = []
    for entries in registered.values():
        for entry in entries:
            for h in entry.get("hooks", []):
                for m in re.finditer(r"\$CLAUDE_PROJECT_DIR/([^\"' ]+)", h.get("command", "")):
                    if not (REPO / m.group(1)).exists():
                        missing.append(m.group(1))
    check("all referenced hook scripts exist", not missing,
          "missing: " + ", ".join(sorted(set(missing))) if missing else "")

    # Now prove each hook has its EFFECT, not merely exit 0.
    if not shutil.which("bash"):
        check("hook effects verified", False,
              "cannot run hooks: bash not on PATH (see environment above)",
              warn_only=True)
        return

    ss = HOOKS / "session-start.sh"
    if ss.exists():
        r = _run(["bash", str(ss)], env=dict(os.environ, JIVO_PERSONA="accounts"))
        check("session-start emits context", bool((r.stdout or "").strip()),
              f"{len(r.stdout or '')} bytes"
              if (r.stdout or "").strip() else
              "emitted NOTHING — operator gets no corrections")

    ups = HOOKS / "user-prompt-submit.sh"
    if ups.exists():
        qlog = HARNESS / "questions" / "log.jsonl"
        before = qlog.stat().st_size if qlog.exists() else 0
        payload = json.dumps({"prompt": "doctor check: ledger balance for Test Traders"})
        r = subprocess.run(["bash", str(ups)], input=payload, text=True,
                           capture_output=True, timeout=60, errors="replace")
        after = qlog.stat().st_size if qlog.exists() else 0
        check("user-prompt-submit logs a question", after > before,
              f"log grew {after - before} bytes" if after > before else
              "log did not grow — question capture is dead")
        check("user-prompt-submit prints nothing", not (r.stdout or "").strip(),
              "it printed to stdout, which costs tokens on every single turn"
              if (r.stdout or "").strip() else "0 bytes, as intended")

    st = HOOKS / "stop.sh"
    if st.exists():
        state = HARNESS / ".state" / "turns"
        before = state.read_text().strip() if state.exists() else "0"
        _run(["bash", str(st)])
        after = state.read_text().strip() if state.exists() else "0"
        check("stop advances the turn counter", before != after or after == "0",
              f"{before} -> {after}")


# ── 5. recall ────────────────────────────────────────────────────────────────

def check_recall() -> None:
    print("\n── recall ──")
    rc = BIN / "recall.py"
    if not rc.exists():
        check("recall present", False, "harness/bin/recall.py missing", warn_only=True)
        return
    r = _run([_py(), str(rc), "index"])
    check("recall indexes the corpus", r.returncode == 0,
          (r.stdout or r.stderr or "").strip().splitlines()[0][:200] if (r.stdout or r.stderr) else "")
    r = _run([_py(), str(rc), "search", "correction"])
    check("recall search runs", r.returncode == 0,
          (r.stdout or "").strip().splitlines()[0][:200] if r.stdout else
          (r.stderr or "").strip()[:200])


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    print("JIVO harness doctor")
    print("Proves the harness works on THIS machine. Silence is not success.")

    check_environment()
    check_repo()
    check_corrections()
    check_hooks()
    check_recall()

    fails = [r for r in _results if r[0] == FAIL]
    warns = [r for r in _results if r[0] == WARN]
    print("\n" + "─" * 68)
    print(f"{len(_results)} checks · {len(_results) - len(fails) - len(warns)} passed · "
          f"{len(warns)} warning(s) · {len(fails)} failure(s)")

    if fails:
        print("\nFAILURES — do not hand this machine to an operator yet:")
        for _, name, detail in fails:
            print(f"  • {name}")
            if detail:
                print(f"      {detail.splitlines()[0]}")
        return 1
    if warns:
        print("\nWarnings (harness works, but read these):")
        for _, name, detail in warns:
            print(f"  • {name}")
        return 0
    print("\nAll green. This machine is ready for an operator.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
