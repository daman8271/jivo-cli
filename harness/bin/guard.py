#!/usr/bin/env python3
"""JIVO guard — the rules that operators cannot quietly change.

A short list of files decides how every operator's Claude behaves: RULE 0 in
CLAUDE.md, the hooks in .claude/settings.json, the watermark stamper, the
corrections digest. This tool pins their SHA-256 into a tracked manifest and
re-checks them, so an edit to any of them is impossible to hide.

What this can and cannot do — read this before trusting it
----------------------------------------------------------
It is tamper-EVIDENT, not tamper-proof. An operator owns their laptop and can
edit any file on it; nothing running on that laptop can prevent that. What this
guarantees is that they cannot do it *silently*:

  * the tooling reports the mismatch and can refuse to run (fail closed),
  * the daily auto-update restores the file from origin, and
  * the mismatch is recorded in their session log, which pushes to `main`.

Prevention lives at a layer this tool cannot reach: a GitHub ruleset that
rejects pushes touching the protected paths. Detection here, prevention there.
Neither substitutes for the other.

This tool NEVER touches SAP or any business system. It reads and writes only
`harness/protected.manifest` and `harness/guard.hash`.

Subcommands
-----------
  seal        Recompute the manifest from the current files (Daman only).
  check       Verify every protected file. Exit 1 if any differs.
  status      Human-readable state.
  set-password  Store a salted hash of the override password.
  verify-password  Exit 0 if the supplied password matches.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import getpass
import hashlib
import hmac
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

# Windows consoles default to cp1252, which cannot encode the characters that
# actually occur in JIVO's data — the rupee sign, en dashes, the check marks in
# this tool's own output. Measured on HO-IT-PC2 (Accounts, 2026-08-22):
# `setup.py --show` died with UnicodeEncodeError on "\u2713" AFTER it had already
# written the identity files, so the operator saw a traceback for a run that had
# in fact succeeded. Same guard as harness.py — force UTF-8 before anything prints.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


HARNESS = Path(__file__).resolve().parent.parent
REPO = HARNESS.parent
MANIFEST = HARNESS / "protected.manifest"   # tracked in git
GUARD_HASH = HARNESS / "guard.hash"         # gitignored, per-machine

# The files that decide how every operator's Claude behaves. Keep this list
# short: a manifest nobody can read is a manifest nobody maintains, and every
# entry added here is a file that can no longer be edited casually.
PROTECTED = [
    "CLAUDE.md",
    ".claude/settings.json",
    "harness/bin/watermark.py",
    "harness/bin/guard.py",
    "harness/bin/harness.py",
    # The self-heal engine itself. Left unprotected, editing this one file
    # disables the repair of all the others.
    "harness/bin/sync.py",
    "harness/hooks/post-write.sh",
    "harness/hooks/session-start.sh",
    "harness/hooks/user-prompt-submit.sh",
    "harness/hooks/stop.sh",
]


def _digest(path: Path) -> str:
    """SHA-256 of a file, with line endings normalised first.

    Git for Windows installs with core.autocrlf=true. Without normalising, a
    file checked out on Windows hashes differently from the same file on macOS
    and every Windows laptop would report tampering on day one. `.gitattributes`
    pins these paths to LF as well; this is the second line of defence for a
    machine with an unexpected git config.
    """
    raw = path.read_bytes()
    if b"\x00" not in raw[:8192]:                      # text, not binary
        raw = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(raw).hexdigest()


def _load_manifest() -> dict:
    if not MANIFEST.exists():
        return {}
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8")).get("files", {})
    except Exception:
        return {}


# ── password ────────────────────────────────────────────────────────────────

def cmd_set_password(args: argparse.Namespace) -> int:
    """Store a salted hash. The plaintext never reaches disk, git, or a log."""
    pw = getpass.getpass("New override password: ")
    if len(pw) < 8:
        print("guard: too short — use at least 8 characters", file=sys.stderr)
        return 2
    if pw != getpass.getpass("Again: "):
        print("guard: passwords did not match", file=sys.stderr)
        return 2
    salt = secrets.token_bytes(16)
    digest = hashlib.sha256(salt + pw.encode()).hexdigest()
    GUARD_HASH.write_text(f"{salt.hex()}${digest}\n", encoding="utf-8")
    try:
        os.chmod(GUARD_HASH, 0o600)
    except Exception:
        pass
    print(f"guard: stored (hash only) → {GUARD_HASH.relative_to(REPO)}")
    print("guard: the plaintext was never written anywhere.")
    return 0


def authorised(supplied: str | None) -> bool:
    if not supplied or not GUARD_HASH.exists():
        return False
    try:
        salt_hex, want = GUARD_HASH.read_text(encoding="utf-8").strip().split("$", 1)
        got = hashlib.sha256(bytes.fromhex(salt_hex) + supplied.encode()).hexdigest()
        return hmac.compare_digest(got, want)
    except Exception:
        return False


def cmd_verify_password(args: argparse.Namespace) -> int:
    pw = args.password or os.environ.get("JIVO_GUARD_PASSWORD")
    if not pw and sys.stdin.isatty():
        pw = getpass.getpass("Override password: ")
    return 0 if authorised(pw) else 1


# ── seal / check ────────────────────────────────────────────────────────────

def cmd_seal(args: argparse.Namespace) -> int:
    files, missing = {}, []
    for rel in PROTECTED:
        path = REPO / rel
        if not path.exists():
            missing.append(rel)
            continue
        files[rel] = _digest(path)

    MANIFEST.write_text(json.dumps({
        "sealed_at": _dt.datetime.now().replace(microsecond=0).isoformat(),
        "algorithm": "sha256(content with CRLF/CR normalised to LF)",
        "files": files,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"guard: sealed {len(files)} files → {MANIFEST.relative_to(REPO)}")
    for rel, dig in sorted(files.items()):
        print(f"  {dig[:12]}  {rel}")
    if missing:
        print("\nguard: NOT sealed (missing):", file=sys.stderr)
        for rel in missing:
            print(f"  {rel}", file=sys.stderr)
    return 0


def _wiring_faults() -> list[str]:
    """Assert the things that must be TRUE, not merely unchanged.

    A hash tells you a file differs; it cannot tell you what was lost. The
    watermark hook has silently disappeared from .claude/settings.json twice
    during development — something rewrites that file and drops the entry — and
    a byte mismatch reported it only as "settings.json changed", which is easy
    to re-seal straight past. When the enforcement is gone, reports go out
    unmarked and nothing complains. So check the wiring itself.
    """
    faults = []
    settings = REPO / ".claude" / "settings.json"
    if not settings.exists():
        return ["`.claude/settings.json` is missing — no hooks run at all"]
    try:
        data = json.loads(settings.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"`.claude/settings.json` is not valid JSON ({exc}) — no hooks run"]

    hooks = data.get("hooks", {})

    def wired(event: str, needle: str) -> bool:
        for entry in hooks.get(event, []):
            for h in entry.get("hooks", []):
                if needle in h.get("command", ""):
                    return True
        return False

    if not wired("PostToolUse", "post-write.sh"):
        faults.append(
            "the WATERMARK hook is not wired — every HTML/Excel report will go "
            "out UNMARKED (expected a PostToolUse hook running "
            "harness/hooks/post-write.sh)")
    if not wired("SessionStart", "session-start.sh"):
        faults.append("the corrections/integrity hook is not wired (SessionStart)")
    if not wired("Stop", "stop.sh"):
        faults.append("the daily sync hook is not wired (Stop) — this machine "
                      "will stop sharing and stop catching up")
    return faults


def _matches_head(rel: str) -> bool:
    """True if the working file is byte-identical to what git has committed.

    This is what separates a real problem from a bookkeeping lapse. A file can
    differ from the manifest for two completely different reasons:

      * someone edited it on this laptop        → tampering, alarm the operator
      * Daman changed it and forgot to re-seal  → the MANIFEST is stale, and the
                                                  operator did nothing wrong

    Without this distinction every operator sees "PROTECTED FILES HAVE CHANGED"
    on a fresh clone the moment a seal falls behind a commit — which is a false
    alarm on day one, and the fastest way to teach everybody to ignore the
    warning that actually matters.
    """
    try:
        blob = subprocess.run(
            ["git", "show", f"HEAD:{rel}"], cwd=REPO,
            capture_output=True, timeout=15,
        )
        if blob.returncode != 0:
            return False
        raw = blob.stdout
        if b"\x00" not in raw[:8192]:
            raw = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        return hashlib.sha256(raw).hexdigest() == _digest(REPO / rel)
    except Exception:
        return False


def _check() -> tuple[list[str], list[str], list[str], list[str]]:
    """Returns (tampered, missing, unsealed, stale).

    `tampered` differs from BOTH the manifest and the committed version — a real
    local edit. `stale` differs from the manifest but matches what is committed,
    so the manifest simply needs re-sealing.
    """
    manifest = _load_manifest()
    tampered, missing, unsealed, stale = [], [], [], []
    for rel, want in manifest.items():
        path = REPO / rel
        if not path.exists():
            missing.append(rel)
        elif _digest(path) != want:
            (stale if _matches_head(rel) else tampered).append(rel)
    for rel in PROTECTED:
        if rel not in manifest and (REPO / rel).exists():
            unsealed.append(rel)
    return tampered, missing, unsealed, stale


def cmd_check(args: argparse.Namespace) -> int:
    if not MANIFEST.exists():
        faults = _wiring_faults()
        if faults:
            for fault in faults:
                print(f"guard: BROKEN — {fault}", file=sys.stderr)
            return 1
        if args.quiet:
            return 0
        print("guard: no manifest yet — run: python3 harness/bin/guard.py seal")
        return 0

    tampered, missing, unsealed, stale = _check()
    faults = _wiring_faults()

    if not tampered and not missing and not faults:
        if not args.quiet:
            n = len(_load_manifest())
            print(f"guard: OK — {n - len(stale)}/{n} protected files match the seal.")
            for rel in stale:
                print(f"guard: note — {rel} matches git but not the seal; "
                      f"Daman should re-seal.")
            for rel in unsealed:
                print(f"guard: note — {rel} is protected but not sealed; re-seal.")
        return 0

    # Loud on purpose. This is the one message that must not be skimmed.
    print("", file=sys.stderr)
    print("  ⚠  JIVO GUARD — PROTECTED FILES HAVE CHANGED", file=sys.stderr)
    print("", file=sys.stderr)
    for rel in tampered:
        print(f"     MODIFIED  {rel}", file=sys.stderr)
    for rel in missing:
        print(f"     DELETED   {rel}", file=sys.stderr)
    for fault in faults:
        print(f"     BROKEN    {fault}", file=sys.stderr)
    print("", file=sys.stderr)
    print("  These files set the rules every operator's Claude follows.", file=sys.stderr)
    print("  If you did not change them deliberately, restore them:", file=sys.stderr)
    print("", file=sys.stderr)
    if tampered or missing:
        print("     git checkout -- " + " ".join(tampered + missing), file=sys.stderr)
    print("", file=sys.stderr)
    print("  Daman: if the change IS yours, re-seal:", file=sys.stderr)
    print("     python3 harness/bin/guard.py seal", file=sys.stderr)
    print("", file=sys.stderr)
    return 1


def cmd_status(args: argparse.Namespace) -> int:
    print(f"manifest : {MANIFEST if MANIFEST.exists() else '(not sealed)'}")
    if MANIFEST.exists():
        try:
            meta = json.loads(MANIFEST.read_text(encoding="utf-8"))
            print(f"sealed   : {meta.get('sealed_at', '?')}")
        except Exception:
            pass
    print(f"password : {'set' if GUARD_HASH.exists() else 'NOT SET (no override possible)'}")
    for fault in _wiring_faults():
        print(f"BROKEN   : {fault}")
    tampered, missing, unsealed, stale = _check()
    print(f"protected: {len(PROTECTED)} listed, {len(tampered)} TAMPERED, "
          f"{len(missing)} missing, {len(stale)} stale-seal, {len(unsealed)} unsealed")
    if stale:
        print(f"           stale (re-seal needed): {', '.join(stale)}")
    return 0 if not (tampered or missing or _wiring_faults()) else 1


def main() -> int:
    ap = argparse.ArgumentParser(
        prog="guard", description="Pin and verify the rules operators cannot change.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("seal", help="recompute the manifest (Daman only)")
    p.set_defaults(func=cmd_seal)

    p = sub.add_parser("check", help="verify protected files; exit 1 on any change")
    p.add_argument("-q", "--quiet", action="store_true", help="only speak up on a problem")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("status", help="show guard state")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("set-password", help="store a salted hash of the override password")
    p.set_defaults(func=cmd_set_password)

    p = sub.add_parser("verify-password", help="exit 0 if the password matches")
    p.add_argument("--password")
    p.set_defaults(func=cmd_verify_password)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
