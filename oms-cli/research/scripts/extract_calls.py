#!/usr/bin/env python3
"""Lens 1 + 3 — sweep every HTTP-client call site in a minified bundle.

Anchoring on the string "/api/" undercounts OMS by ~3.5x, because the axios
instance carries the /api prefix in its baseURL:

    var Ea = `https://oms.jivo.in/api`.replace(/\\/+$/, ``)
    var Y  = Ta.create({ baseURL: Ea, ... })
    Y.get(`/auth/profile/`)          <- no "/api/" anywhere

So we anchor on the VERB instead: find every `.get(` / `.post(` / `.put(` /
`.patch(` / `.delete(` / `.request(` whose FIRST ARGUMENT is a string or
template literal beginning with "/". That is receiver-agnostic, so it cannot
be defeated by a minifier renaming the instance between builds, and it still
excludes lodash-style `.get(obj, "a.b")` (second arg, no leading slash).

The receiver identifier is recorded for every hit so the caller can prove which
alias is the HTTP client and quarantine anything else.

usage: extract_calls.py <bundle.js> [more.js ...]   -> JSON on stdout
"""
import json
import re
import sys

VERBS = ("get", "post", "put", "patch", "delete", "head", "options", "request")

# <receiver>.<verb>(   — receiver is a minified identifier or a `)`/`]` tail
CALL = re.compile(r"([A-Za-z_$][\w$]*)\.(" + "|".join(VERBS) + r")\(")


def read_literal(src, i):
    """Read a JS string or template literal starting at src[i].

    Returns (text, end_index) where text is the literal's raw body with the
    quotes stripped, or (None, i) if src[i] does not open a literal.
    Handles escapes, and for templates handles nested ${...} that may itself
    contain a nested template literal.
    """
    if i >= len(src):
        return None, i
    q = src[i]
    if q not in "\"'`":
        return None, i
    out, j, n = [], i + 1, len(src)
    while j < n:
        ch = src[j]
        if ch == "\\":
            out.append(src[j:j + 2])
            j += 2
            continue
        if ch == q:
            return "".join(out), j + 1
        if q == "`" and ch == "$" and j + 1 < n and src[j + 1] == "{":
            depth, k = 1, j + 2
            while k < n and depth:
                c = src[k]
                if c == "\\":
                    k += 2
                    continue
                if c in "\"'`":                    # skip a nested literal whole
                    _, k = read_literal(src, k)
                    continue
                if c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                k += 1
            out.append(src[j:k])
            j = k
            continue
        out.append(ch)
        j += 1
    return None, i                                  # unterminated


def arg_list_end(src, open_paren):
    """Index just past the ')' that closes the call opened at src[open_paren].

    Balances (), [] and {} and skips string/template literals whole, so a brace
    or paren inside a literal cannot end the scan early.
    """
    depth, j, n = 0, open_paren, len(src)
    while j < n:
        c = src[j]
        if c in "\"'`":
            _, j = read_literal(src, j)
            continue
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return min(n, open_paren + 2000)


def scan(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    hits = []
    for m in CALL.finditer(src):
        recv, verb = m.group(1), m.group(2)
        lit, end = read_literal(src, m.end())
        if lit is None or not lit.startswith("/"):
            continue
        # The call's OWN argument list, and nothing after it.
        #
        # This used to be a flat `end + 160` window, which is wrong in a
        # minified bundle where the next call begins immediately: the window
        # ran past the closing paren into the following method and the params
        # object found there was credited to THIS path. It mis-attributed 6 of
        # 15 param sets — `mode` was credited to /orders/status/ when it
        # belongs to /orders/status-tracking/, `category` to /sap/addresses/
        # when it belongs to /sap/parties/category/, `flow_type` to
        # /orders/staff-products/ when it belongs to /orders/flow-config/.
        # Every one of those would have shipped as a real flag on the wrong
        # command. Balancing to the actual ')' removes the guesswork.
        args_end = arg_list_end(src, m.end() - 1)
        hits.append({
            "file": path.rsplit("/", 1)[-1],
            "receiver": recv,
            "method": verb.upper(),
            "raw_path": lit,
            "offset": m.start(),
            "context": src[m.start():args_end],
            # kept separately: useful for reading intent, never for params
            "trailing_context": src[args_end:min(len(src), args_end + 120)],
        })
    return hits


def main():
    all_hits = []
    for p in sys.argv[1:]:
        all_hits.extend(scan(p))
    json.dump(all_hits, sys.stdout, indent=1)


if __name__ == "__main__":
    main()
