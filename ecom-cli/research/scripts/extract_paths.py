#!/usr/bin/env python3
"""Extract API paths from rolldown-minified SPA chunks.

Rolldown normalises EVERY string literal to a backtick template, so the
factory literal-vs-template extraction bias does not apply here. The bias
that DOES apply is nested template literals: a path containing
`${x ? `a` : `b`}` closes the outer backtick early under a naive
`` `[^`]*` `` regex and truncates the path mid-interpolation.

This scanner walks characters and tracks template-literal nesting depth so
`${ ... `inner` ... }` stays inside the outer literal.

usage: extract_paths.py <chunk-dir> <out.jsonl>
"""
import json
import os
import re
import sys


def scan_templates(src):
    """Yield (start_index, raw_text_without_backticks) for every top-level
    template literal in src, handling nested ${ `...` } correctly."""
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c == "\\":
            i += 2
            continue
        if c != "`":
            i += 1
            continue
        # start of a template literal
        start = i
        i += 1
        depth = 0          # ${ } nesting depth
        buf = []
        while i < n:
            c = src[i]
            if c == "\\":
                buf.append(src[i:i + 2])
                i += 2
                continue
            if c == "`" and depth == 0:
                i += 1
                break
            if c == "$" and i + 1 < n and src[i + 1] == "{":
                depth += 1
                buf.append("${")
                i += 2
                continue
            if c == "}" and depth > 0:
                depth -= 1
                buf.append("}")
                i += 1
                continue
            if c == "`" and depth > 0:
                # nested template inside an interpolation - consume it whole
                j, d2 = i + 1, 0
                while j < n:
                    if src[j] == "\\":
                        j += 2
                        continue
                    if src[j] == "$" and j + 1 < n and src[j + 1] == "{":
                        d2 += 1
                        j += 2
                        continue
                    if src[j] == "}" and d2 > 0:
                        d2 -= 1
                        j += 1
                        continue
                    if src[j] == "`" and d2 == 0:
                        j += 1
                        break
                    j += 1
                buf.append(src[i:j])
                i = j
                continue
            buf.append(c)
            i += 1
        yield start, "".join(buf)


API_RE = re.compile(r"^/api/[A-Za-z0-9_\-./${}?=&:,()\[\]|+*'\"`? ]*$")


def main():
    chunk_dir, out_path = sys.argv[1], sys.argv[2]
    recs = []
    for fn in sorted(os.listdir(chunk_dir)):
        if not fn.endswith(".js"):
            continue
        src = open(os.path.join(chunk_dir, fn), encoding="utf-8", errors="replace").read()
        for pos, tpl in scan_templates(src):
            if not tpl.startswith("/api/"):
                continue
            if len(tpl) > 300:
                continue
            recs.append({
                "chunk": fn,
                "raw": tpl,
                "ctx": src[max(0, pos - 220):pos + len(tpl) + 260],
            })
    with open(out_path, "w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    print(f"{len(recs)} raw occurrences from {len({r['chunk'] for r in recs})} chunks -> {out_path}")
    print(f"{len({r['raw'] for r in recs})} distinct raw path templates")


if __name__ == "__main__":
    main()
