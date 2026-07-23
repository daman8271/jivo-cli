"""READ-ONLY LAW enforcement — the build fails if any write surface appears.

Run: python3 -m pytest tests/  (or) python3 tests/test_readonly.py
This is the automated guard referenced by docs/READ_ONLY_LAW.md.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PKG = ROOT / "jsap"
MODULES_DIR = PKG / "modules"

# A path is write-shaped when its LEAF segment (the API action, after the final
# "/") STARTS WITH a mutating verb. Leaf-prefix matching — not substring — so a
# read like GetRejectedDataByUserId ("Get...") or a controller like
# DocumentDispatch ("Document...") is correctly treated as a read, while
# RejectDocument / InsertBPmasterData / SaveAllAttachments are caught.
MUTATING_PREFIXES = (
    "insert",
    "save",
    "update",
    "delete",
    "add",
    "create",
    "submit",
    "reject",
    "approve",
    "mark",
    "upload",
    "import",
    "unlock",
    "register",
    "attach",
    "dispatch",
    "set",
    "remove",
    "put",
    "post",
    "patch",
    "edit",
    "cancel",
    "assign",
    "revoke",
    "send",
    "changelock",
    "removelock",
)


def _is_write_path(path: str) -> bool:
    leaf = path.split("?", 1)[0].rstrip("/").rsplit("/", 1)[-1].lower()
    return any(leaf.startswith(v) for v in MUTATING_PREFIXES)


# Genuinely-mutating HTTP method literals that must never appear in module files.
# POST is allowed: it routes through client.read_post, which refuses any path
# whose leaf action is not a read verb (and test_modules_contain_no_write_paths
# independently proves every module path is read-shaped). There is no read_put /
# read_patch / read_delete — those verbs only ever mutate.
METHOD_RE = re.compile(r"""method\s*=\s*['"](?:PUT|PATCH|DELETE)['"]""", re.I)


def _module_files() -> list[Path]:
    return sorted(
        p
        for p in MODULES_DIR.glob("*.py")
        if not p.name.startswith("_") and p.name != "__init__.py"
    )


def test_parser_builds():
    from jsap.cli import build_parser

    build_parser()  # raises on any registration/import error


def test_client_exposes_no_write_verbs():
    from jsap.client import JsapClient

    for verb in (
        "post",
        "put",
        "patch",
        "delete",
        "write",
        "create",
        "update",
        "insert",
    ):
        assert not hasattr(JsapClient, verb), (
            f"JsapClient must not expose a `{verb}` method"
        )


def test_modules_contain_no_write_paths():
    offenders = []
    for f in _module_files():
        # Only inspect string literals that look like API paths.
        for m in re.finditer(r"""["']((?:/[^"']*))["']""", f.read_text()):
            path = m.group(1)
            if path.startswith("/api/") or path.startswith("/"):
                if _is_write_path(path):
                    offenders.append(f"{f.name}: {path}")
    assert not offenders, "Write-shaped endpoint paths found:\n" + "\n".join(offenders)


def test_modules_use_no_mutating_http_methods():
    offenders = [f.name for f in _module_files() if METHOD_RE.search(f.read_text())]
    assert not offenders, f"Mutating HTTP method literal in: {offenders}"


def test_read_post_refuses_mutating_leaves():
    """The guarded POST-to-read path must reject any non-read action verb."""
    from jsap.client import JsapClient, JsapError

    c = JsapClient(company=1)
    c._authed = True  # skip real bootstrap; we only want the guard to fire
    for bad in (
        "/api/Tickets/CreateTicket",
        "/api/Tickets/AssignTicket",
        "/api/DocumentDispatch/SaveAllAttachments",
        "/api/BPmaster/InsertBPmasterData",
    ):
        try:
            c.read_post(bad, {})
        except JsapError as e:
            assert "READ-ONLY" in str(e)
        else:
            raise AssertionError(f"read_post should have refused {bad}")


def test_client_bootstrap_is_the_only_non_get():
    """client.py may POST only to the two sanctioned bootstrap paths."""
    src = (PKG / "client.py").read_text()
    posts = re.findall(
        r"""_request\(\s*['"](POST|PUT|PATCH|DELETE)['"]\s*,\s*['"]([^'"]+)['"]""", src
    )
    allowed = {
        "/api/auth/Login",
        "/websession/set",
        "/websession/updateSelectedCompany",
    }
    bad = [f"{meth} {path}" for meth, path in posts if path not in allowed]
    assert not bad, f"Non-GET calls outside session bootstrap: {bad}"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} read-only checks passed")
    sys.exit(1 if failed else 0)
