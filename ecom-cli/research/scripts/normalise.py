#!/usr/bin/env python3
"""Canonical path normaliser — the single source of truth for comparing
harvested paths against the shipped spec, the denylist and the probe results.

Skill rule 8: exclusion lists must match on NORMALISED forms. Every consumer
imports norm() from here so a rename of {id} -> {entry_id} can never make a
denylist fail open.

Normal form:
  - strip a query string
  - collapse every ${...} interpolation and every {name} placeholder to {}
  - collapse a run of adjacent placeholders
  - strip the trailing slash (but never reduce "/" to "")
"""
import re

_BRACE = re.compile(r"\{[^{}]*\}")


def _strip_interpolations(p):
    """Replace every ${...} with {} by walking characters and balancing
    braces. A regex cannot do this: an interpolation may itself contain a
    nested template literal (`${a ? `x` : `y`}`) whose braces and backticks
    break any bounded pattern.

    One interpolation shape is NOT a path parameter and must not become one:

        `/api/shipment/inventory/${e ? `?warehouse=${e}` : ``}`

    that expands to a QUERY STRING or to nothing, so the real path is
    `/api/shipment/inventory/`. Treating it as `{}` invents a path segment,
    marks the endpoint unprobeable, and then reports the genuine collection
    root as "shipped but no longer called" - which is exactly the
    fails-open-on-a-rename failure skill rule 8 warns about. Six ecom paths
    hit this. An interpolation whose body opens a nested template with `?`
    is a query-string builder and is dropped, not placeholdered.
    """
    out, i, n = [], 0, len(p)
    while i < n:
        if p[i] == "$" and i + 1 < n and p[i + 1] == "{":
            depth, j = 1, i + 2
            while j < n and depth:
                ch = p[j]
                if ch == "\\":
                    j += 2
                    continue
                if ch == "`":                 # skip a nested template whole
                    j += 1
                    while j < n and p[j] != "`":
                        j += 2 if p[j] == "\\" else 1
                    j += 1
                    continue
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                j += 1
            body = p[i + 2:j - 1]
            if "`?" in body or body.strip().startswith("?"):
                out.append("")                # query-string builder, not a param
            else:
                out.append("{}")
            i = j
            continue
        out.append(p[i])
        i += 1
    return "".join(out)


def norm(p):
    p = (p or "").strip()
    p = _strip_interpolations(p)
    p = p.split("?", 1)[0]
    p = _BRACE.sub("{}", p)
    p = re.sub(r"/{2,}", "/", p)
    if len(p) > 1:
        p = p.rstrip("/")
    return p


def domain_of(p):
    """Domain from the PATH, never from a lens's own label."""
    parts = [x for x in norm(p).split("/") if x]
    # ['api', '<domain>', ...]
    if len(parts) >= 2 and parts[0] == "api":
        return parts[1]
    return parts[0] if parts else "unknown"


if __name__ == "__main__":
    tests = [
        ("/api/shipment/appointments/", "/api/shipment/appointments"),
        ("/api/shipment/all-appointments/${t}", "/api/shipment/all-appointments/{}"),
        ("/api/dashboard/table-row/${e}", "/api/dashboard/table-row/{}"),
        ("/api/x/{id}/y", "/api/x/{}/y"),
        ("/api/x/{entry_id}/y", "/api/x/{}/y"),
        ("/api/p/${encodeURIComponent(t)}/items", "/api/p/{}/items"),
        ("/api/a?b=c", "/api/a"),
        ("/api/z/${a ? `x` : `y`}/w", "/api/z/{}/w"),
        # query-string builders must NOT become path parameters
        ("/api/shipment/all-appointments/${t?`?${t}`:``}",
         "/api/shipment/all-appointments"),
        ("/api/shipment/inventory/${e?`?warehouse=${encodeURIComponent(e)}`:``}",
         "/api/shipment/inventory"),
        ("/api/shipment/shipments/deletion-log/${e?`?limit=${e}`:``}",
         "/api/shipment/shipments/deletion-log"),
        # a genuine path parameter next to one must still survive
        ("/api/shipment/appointments/${e}/families/",
         "/api/shipment/appointments/{}/families"),
    ]
    bad = 0
    for src, want in tests:
        got = norm(src)
        ok = got == want
        bad += not ok
        print(("ok  " if ok else "FAIL"), src, "->", got, "" if ok else f"(want {want})")
    raise SystemExit(1 if bad else 0)
