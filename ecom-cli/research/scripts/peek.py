#!/usr/bin/env python3
"""Bounded context peek into a minified single-line bundle.

`grep -oE '.{0,N}PAT.{0,M}'` backtracks catastrophically on a megabyte
single-line file (it hung for >120s here). Plain str.find does the same job
in milliseconds. Use this instead of grep for every bundle inspection.

usage: peek.py <file> <literal-substring> [before=200] [after=300] [max=8]
"""
import sys

path, needle = sys.argv[1], sys.argv[2]
before = int(sys.argv[3]) if len(sys.argv) > 3 else 200
after = int(sys.argv[4]) if len(sys.argv) > 4 else 300
limit = int(sys.argv[5]) if len(sys.argv) > 5 else 8

src = open(path, encoding="utf-8", errors="replace").read()
i, n = 0, 0
while n < limit:
    i = src.find(needle, i)
    if i < 0:
        break
    print(f"--- @{i} ---")
    print(src[max(0, i - before):i + len(needle) + after])
    print()
    i += 1
    n += 1
if n == 0:
    print(f"(no occurrence of {needle!r} in {path})")
