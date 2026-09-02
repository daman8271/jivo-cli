#!/usr/bin/env python3
"""jivo hub - find the CLI that answers a question, and check it actually runs.

Borrowed from CLI-Anything's CLI-Hub (clianything.cc): the part that matters is
runtime discovery, so an agent that does not know a tool exists can find it
mid-task instead of guessing or hand-rolling a query.

No network. No install of anything external. It reads hub/registry.json,
resolves paths against this checkout, and shells out to the CLI you pick.

    hub.py list                      every CLI, grouped by system
    hub.py search "ledger balance"   which CLI answers this?
    hub.py info sapb1                what it does, how to run it, its traps
    hub.py doctor [name]             is it built and does it respond?
    hub.py run sapb1 -- doctor       run it without knowing where it lives
"""
import json
import os
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REGISTRY = os.path.join(os.path.dirname(HERE), "registry.json")


def load():
    with open(REGISTRY, encoding="utf-8") as fh:
        return json.load(fh)


def resolve(cli):
    """Absolute path to the binary, preferring the .exe on Windows."""
    rel = cli["bin"]
    if os.name == "nt" and cli.get("win"):
        win = os.path.join(ROOT, cli["win"])
        if os.path.exists(win):
            return win
    p = os.path.join(ROOT, rel)
    if os.name == "nt" and not os.path.exists(p) and os.path.exists(p + ".exe"):
        return p + ".exe"
    return p


def installed(cli):
    return os.path.exists(resolve(cli))


def score(cli, terms):
    """Rank a CLI against the search terms. Keywords weigh most, then what it
    answers, then the system name. Substring matching on purpose - an operator
    types 'aging' and the keyword says 'ageing'."""
    hay_kw = " ".join(cli.get("keywords", [])).lower()
    hay_ans = (cli.get("answers", "") + " " + cli.get("name", "")).lower()
    hay_sys = cli.get("system", "").lower()
    total = 0
    for t in terms:
        if t in hay_kw:
            total += 5
        if t in hay_ans:
            total += 3
        if t in hay_sys:
            total += 2
    return total


def w(name, writes):
    return "WRITE" if writes else "read"


def cmd_list(reg, args):
    for cli in reg["clis"]:
        mark = " " if installed(cli) else "!"
        print("%s %-14s %-5s %-46s %s" % (mark, cli["name"], w(cli["name"], cli["writes"]),
                                          cli["system"][:46], cli["bin"]))
    print("\n%d CLIs. '!' = not built in this checkout - run `hub.py doctor` for why." % len(reg["clis"]))


def cmd_search(reg, args):
    if not args:
        print("usage: hub.py search \"<what you want to know>\"", file=sys.stderr)
        return 2
    terms = [t for t in " ".join(args).lower().replace(",", " ").split() if len(t) > 2]
    hits = [(score(c, terms), c) for c in reg["clis"]]
    hits = sorted([h for h in hits if h[0] > 0], key=lambda h: -h[0])
    if not hits:
        print("Nothing in the registry matches that.")
        print("If no CLI covers it, that is a gap worth building - see .claude/skills/press-desktop")
        return 1
    for sc, cli in hits[:5]:
        flag = "" if installed(cli) else "  [NOT BUILT]"
        print("\n%-14s (%s)%s" % (cli["name"], w(cli["name"], cli["writes"]), flag))
        print("  system : %s" % cli["system"])
        print("  answers: %s" % cli["answers"])
        print("  run    : %s" % run_prefix(cli))
        if cli.get("caution"):
            print("  TRAP   : %s" % cli["caution"])
    return 0


def run_prefix(cli):
    if cli.get("run"):
        return cli["run"]
    return cli["bin"]


def cmd_info(reg, args):
    if not args:
        print("usage: hub.py info <name>", file=sys.stderr)
        return 2
    name = args[0]
    for cli in reg["clis"]:
        if cli["name"] == name:
            print("%s  -  %s" % (cli["name"], cli["system"]))
            print("\nanswers   : %s" % cli["answers"])
            print("language  : %s" % cli["lang"])
            print("binary    : %s%s" % (cli["bin"], "" if installed(cli) else "   [NOT BUILT]"))
            print("run       : %s" % run_prefix(cli))
            print("writes    : %s - %s" % ("YES" if cli["writes"] else "no", cli["write_note"]))
            print("check     : %s" % cli["doctor"])
            if cli.get("build"):
                print("build     : %s" % cli["build"])
            if cli.get("caution"):
                print("\nTRAP      : %s" % cli["caution"])
            if cli.get("docs"):
                print("\ndocs      : %s" % "\n            ".join(cli["docs"]))
            if cli.get("skills"):
                print("skills    : %s" % ", ".join(cli["skills"]))
            return 0
    print("No CLI named %r. Try: hub.py list" % name, file=sys.stderr)
    return 1


def cmd_doctor(reg, args):
    """Report what is actually on disk. The registry says what SHOULD exist;
    this is the only part that knows what DOES."""
    probe = "--probe" in args
    args = [a for a in args if a != "--probe"]
    wanted = args[0] if args else None
    missing = 0
    for cli in reg["clis"]:
        if wanted and cli["name"] != wanted:
            continue
        path = resolve(cli)
        if not os.path.exists(path):
            print("MISSING  %-14s %s" % (cli["name"], cli["bin"]))
            if cli.get("build"):
                print("         build it: %s" % cli["build"])
            missing += 1
            continue
        if not probe:
            print("built    %-14s %s" % (cli["name"], cli["bin"]))
            continue
        cmd = cli["doctor"]
        try:
            r = subprocess.run(shlex.split(cmd), cwd=ROOT, capture_output=True,
                               timeout=25, text=True)
            state = "OK" if r.returncode == 0 else "EXIT %d" % r.returncode
        except subprocess.TimeoutExpired:
            state = "TIMEOUT"
        except Exception as exc:                      # noqa: BLE001 - report, never raise
            state = "ERROR %s" % exc.__class__.__name__
        print("%-8s %-14s %s" % (state, cli["name"], cmd))
    if missing:
        print("\n%d not built. Nothing is broken - they just have not been compiled here." % missing)
    return 0


def cmd_run(reg, args):
    if not args:
        print("usage: hub.py run <name> -- <args...>", file=sys.stderr)
        return 2
    name = args[0]
    rest = args[1:]
    if rest and rest[0] == "--":
        rest = rest[1:]
    for cli in reg["clis"]:
        if cli["name"] == name:
            path = resolve(cli)
            if cli.get("run"):
                argv = shlex.split(cli["run"]) + rest
            else:
                if not os.path.exists(path):
                    print("%s is not built. %s" % (name, cli.get("build", "no build command recorded")),
                          file=sys.stderr)
                    return 3
                argv = [path] + rest
            return subprocess.call(argv, cwd=ROOT)
    print("No CLI named %r" % name, file=sys.stderr)
    return 1


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    reg = load()
    verb, rest = argv[0], argv[1:]
    table = {"list": cmd_list, "search": cmd_search, "info": cmd_info,
             "doctor": cmd_doctor, "run": cmd_run}
    if verb not in table:
        print("Unknown command %r. One of: %s" % (verb, ", ".join(table)), file=sys.stderr)
        return 2
    return table[verb](reg, rest)


if __name__ == "__main__":
    sys.exit(main())
