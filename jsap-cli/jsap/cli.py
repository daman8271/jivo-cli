"""jsap — a READ-ONLY command-line interface to the JSAP platform.

Every command performs GET reads only (see jsap/client.py and the READ-ONLY
LAW). One command group per JSAP module; one subcommand per read endpoint.
"""

from __future__ import annotations

import argparse
import sys

from . import output
from ._reg import set_common
from .client import JsapClient, JsapError
from .modules import ALL_MODULES


def _add_global_flags(p: argparse.ArgumentParser, *, suppress: bool = False) -> None:
    # On the leaf/parent parser we suppress defaults so that a flag given BEFORE
    # the subcommand (parsed by the root) is not silently overwritten by the
    # subparser's default. Real defaults live only on the root parser.
    def d(v):
        return argparse.SUPPRESS if suppress else v

    p.add_argument(
        "-c",
        "--company",
        type=int,
        default=d(1),
        choices=(1, 2),
        help="Company scope: 1=JIVO OIL, 2=JIVO BEVERAGE",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=d(False),
        help="Emit JSON instead of a table",
    )
    p.add_argument(
        "--raw",
        action="store_true",
        default=d(False),
        help="Show the full {success,message,data} envelope",
    )
    p.add_argument(
        "--select",
        metavar="F1,F2",
        default=d(None),
        help="Comma-separated fields to keep (lists of objects)",
    )
    p.add_argument(
        "--limit", type=int, metavar="N", default=d(None), help="Cap rows shown"
    )
    p.add_argument("--timeout", type=int, default=d(30), help="HTTP timeout (s)")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="jsap",
        description="Read-only CLI for the JSAP platform (JIVO). GET reads only.",
        epilog="Company: 1=JIVO OIL (default), 2=JIVO BEVERAGE. "
        "Credentials come from the project .env.",
    )
    _add_global_flags(p)

    # Parent parser so the same flags are also accepted AFTER the subcommand.
    # suppress=True is essential: without it, the subparser re-applies its own
    # defaults over whatever the root already parsed (silent wrong --company).
    common = argparse.ArgumentParser(add_help=False)
    _add_global_flags(common, suppress=True)
    set_common(common)

    sub = p.add_subparsers(dest="_group", metavar="<module>")
    sub.required = True
    for module in ALL_MODULES:
        module.register(sub)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    run = getattr(args, "_run", None)
    if run is None:
        parser.print_help()
        return 2

    client = JsapClient(company=args.company, timeout=args.timeout)
    if getattr(args, "raw", False):
        # --raw forces envelope visibility for this invocation, for both the
        # GET and the guarded POST-to-read paths.
        _orig_get, _orig_post = client.get, client.read_post

        def _get(path, params=None, unwrap=True):
            return _orig_get(path, params, unwrap=False)

        def _post(path, body=None, *, unwrap=True):
            return _orig_post(path, body, unwrap=False)

        client.get = _get  # type: ignore[method-assign]
        client.read_post = _post  # type: ignore[method-assign]

    try:
        data = run(client, args)
    except JsapError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130

    output.render(data, as_json=args.json, select=args.select, limit=args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
