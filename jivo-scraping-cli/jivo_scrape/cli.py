"""jivo-scrape dispatcher — discovers and routes to command modules.

Each module in jivo_scrape.commands exposes register(subparsers) which attaches
its own argparse subparser and sets func=run via set_defaults.
"""

import argparse
import importlib
import os
import sys

from jivo_scrape import __version__

COMMANDS = [
    "price",
    "avail",
    "compare",
    "match",
    "drr",
    "today",
    "files",
    "doctor",
    "product",
    "history",
    "asof",
    "runs",
    "vault",
    "reports",
]


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="jivo-scrape",
        description="The counter clerk at the JIVO data godown — ask it about "
        "today's (or any day's) prices, availability, price-match and DRR data.",
    )
    parser.add_argument(
        "--version", action="version", version=f"jivo-scrape {__version__}"
    )
    sub = parser.add_subparsers(dest="cmd", metavar="<command>")
    for name in COMMANDS:
        importlib.import_module(f"jivo_scrape.commands.{name}").register(sub)
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 2
    try:
        rc = args.func(args) or 0
        # Flush inside the try so a closed pipe surfaces HERE (catchable),
        # not at interpreter-shutdown flush (uncatchable -> exit 120 + noise).
        sys.stdout.flush()
        return rc
    except BrokenPipeError:
        # Point stdout's fd at devnull so the shutdown re-flush can't raise.
        try:
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except OSError:
            pass
        return 0
    except ValueError as e:
        print(f"jivo-scrape: bad argument: {e}", file=sys.stderr)
        return 2
    except PermissionError as e:
        print(f"jivo-scrape: source unreadable: {e}", file=sys.stderr)
        return 3
    except IsADirectoryError as e:
        # A --show target that resolves to a directory: in-root but not a note.
        # Sibling of FileNotFoundError/PermissionError (all OSError), so it needs
        # its own clause -- map it to the same "source problem" exit, no crash.
        print(f"jivo-scrape: source is a directory, not a note: {e}", file=sys.stderr)
        return 3
    except FileNotFoundError as e:
        print(f"jivo-scrape: source missing: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
