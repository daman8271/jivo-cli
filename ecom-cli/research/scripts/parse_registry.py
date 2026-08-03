#!/usr/bin/env python3
"""Lens 1 (primary) — parse ecom's API service modules into typed entries.

Ecom has no single frozen ENDPOINTS constant like factory. It has two
hand-written service modules whose exported objects hold one arrow function
per endpoint:

    var Ae = { getStats: e => X(`/api/platform/${e}/stats`), ... }

The helper identity IS the HTTP verb, resolved from the module source:

    X(path, params)   -> GET   (we(Ce(path,params)); fetch has no method)
    Z(path, body)     -> POST  (method:`POST`, JSON body)
    Te(path, form)    -> POST  (multipart upload)
    Ee(path, body)    -> POST  (export -> blob)
    i(VERB, path)     -> VERB  (shipmentAPI: verb is the first argument)

That makes verb classification precise rather than inferred, which is what
RULE 0 turns on: only GET entries may ever be published.

usage: parse_registry.py <bundle-dir> <out.jsonl>
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalise import norm, domain_of  # noqa: E402

# helper symbol -> verb, for api-*.js. Resolved by reading each definition.
HELPER_VERB = {"X": "GET", "Z": "POST", "Te": "POST", "Ee": "POST"}


def find_key(src, idx):
    """Walk backwards from a helper call to the object key that owns it.

    `getTopSkus:(e={})=>X(` -> "getTopSkus". Returns (key, owner_hint)."""
    j = idx
    # skip back over the arrow-function header: (args)=>
    seg = src[max(0, j - 160):j]
    m = re.search(r"([A-Za-z_$][A-Za-z0-9_$]*)\s*:\s*(?:async\s*)?\(?[^()]*\)?\s*=>\s*(?:\{[^{}]*return\s*)?$", seg)
    if m:
        return m.group(1)
    m = re.search(r"([A-Za-z_$][A-Za-z0-9_$]*)\s*:\s*(?:async\s*)?(?:function)?\s*\(?[^()]{0,60}\)?\s*=>\s*$", seg)
    if m:
        return m.group(1)
    m = re.findall(r"([A-Za-z_$][A-Za-z0-9_$]*)\s*:", seg)
    return m[-1] if m else None


def owner_of(src, idx):
    """Nearest preceding `var XX={` / `,XX={` object-literal assignment."""
    seg = src[max(0, idx - 6000):idx]
    ms = list(re.finditer(r"(?:var|let|const|,|;)\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*\{", seg))
    return ms[-1].group(1) if ms else None


def template_at(src, i):
    """Read the backtick template starting at src[i] == '`', nesting-aware."""
    assert src[i] == "`"
    i += 1
    depth, buf = 0, []
    n = len(src)
    while i < n:
        c = src[i]
        if c == "\\":
            buf.append(src[i:i + 2]); i += 2; continue
        if c == "`" and depth == 0:
            return "".join(buf), i + 1
        if c == "$" and i + 1 < n and src[i + 1] == "{":
            depth += 1; buf.append("${"); i += 2; continue
        if c == "}" and depth > 0:
            depth -= 1; buf.append("}"); i += 1; continue
        if c == "`" and depth > 0:
            j, d2 = i + 1, 0
            while j < n:
                if src[j] == "\\":
                    j += 2; continue
                if src[j] == "$" and j + 1 < n and src[j + 1] == "{":
                    d2 += 1; j += 2; continue
                if src[j] == "}" and d2 > 0:
                    d2 -= 1; j += 1; continue
                if src[j] == "`" and d2 == 0:
                    j += 1; break
                j += 1
            buf.append(src[i:j]); i = j; continue
        buf.append(c); i += 1
    return "".join(buf), i


def query_params(src, after_idx):
    """Literal query-param names passed to the GET helper, e.g.
    X(`/api/x`,{sku:t}) -> ['sku']. Only literal keys; a spread of a caller
    object yields nothing, which is correct - we must never invent a param."""
    seg = src[after_idx:after_idx + 260]
    if not seg.startswith(","):
        return []
    m = re.match(r",\s*\{([^{}]*)\}", seg)
    if not m:
        return []
    return [k for k in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*:", m.group(1))]


def parse_api_module(path, out):
    src = open(path, encoding="utf-8", errors="replace").read()
    fn = os.path.basename(path)
    for m in re.finditer(r"([A-Za-z_$][A-Za-z0-9_$]{0,3})\(`", src):
        sym = m.group(1)
        if sym not in HELPER_VERB:
            continue
        tick = m.end() - 1
        raw, end = template_at(src, tick)
        if not raw.startswith("/api/"):
            continue
        out.append({
            "chunk": fn,
            "lens": "registry",
            "raw_path": raw,
            "path": norm(raw),
            "method": HELPER_VERB[sym],
            "helper": sym,
            "fn_name": find_key(src, m.start()),
            "service_var": owner_of(src, m.start()),
            "query_params": query_params(src, end),
            "domain": domain_of(raw),
            "evidence": src[max(0, m.start() - 90):end + 90],
        })


def parse_shipment_module(path, out):
    """shipmentAPI: i(`VERB`, `/api/...`) - verb is explicit."""
    src = open(path, encoding="utf-8", errors="replace").read()
    fn = os.path.basename(path)
    for m in re.finditer(r"([A-Za-z_$][A-Za-z0-9_$]{0,3})\(`(GET|POST|PUT|PATCH|DELETE)`\s*,\s*`", src):
        tick = m.end() - 1
        raw, end = template_at(src, tick)
        if not raw.startswith("/api/"):
            continue
        out.append({
            "chunk": fn,
            "lens": "registry",
            "raw_path": raw,
            "path": norm(raw),
            "method": m.group(2),
            "helper": m.group(1),
            "fn_name": find_key(src, m.start()),
            "service_var": owner_of(src, m.start()),
            "query_params": sorted(set(re.findall(r"[?&]([A-Za-z_][A-Za-z0-9_]*)=", raw))),
            "domain": domain_of(raw),
            "evidence": src[max(0, m.start() - 90):end + 90],
        })
    # shipmentAPI also builds some paths then calls i(verb, url)
    for m in re.finditer(r"([A-Za-z_$][A-Za-z0-9_$]{0,3})\(`(GET|POST|PUT|PATCH|DELETE)`\s*,\s*([A-Za-z_$][A-Za-z0-9_$]*)\b", src):
        out.append({
            "chunk": fn, "lens": "registry-indirect", "raw_path": None,
            "path": None, "method": m.group(2), "helper": m.group(1),
            "fn_name": find_key(src, m.start()), "service_var": owner_of(src, m.start()),
            "query_params": [], "domain": None,
            "evidence": src[max(0, m.start() - 320):m.end() + 120],
        })


def main():
    bundle, out_path = sys.argv[1], sys.argv[2]
    out = []
    parse_api_module(os.path.join(bundle, "api-De44ElJm.js"), out)
    parse_shipment_module(os.path.join(bundle, "shipmentAPI-DKVOXJWL.js"), out)
    with open(out_path, "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    direct = [r for r in out if r["path"]]
    import collections
    print(f"{len(out)} entries ({len(direct)} with a resolved path, "
          f"{len(out) - len(direct)} indirect)")
    print("verbs:", collections.Counter(r["method"] for r in out))
    print("GET-capable distinct paths:",
          len({r["path"] for r in direct if r["method"] == "GET"}))
    print("distinct paths:", len({r["path"] for r in direct}))
    print("domains:", collections.Counter(r["domain"] for r in direct))
    print("unnamed fn_name:", sum(1 for r in out if not r["fn_name"]))


if __name__ == "__main__":
    main()
