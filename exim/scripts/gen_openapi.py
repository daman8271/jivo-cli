#!/usr/bin/env python3
"""Regenerate cli/exim-openapi.json (read-only surface) from endpoints.json."""

import json
import re
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = json.load(open(f"{ROOT}/endpoints.json"))
eps = [e for e in spec["endpoints"] if e["kind"] in ("read", "detail")]
# Defense in depth: this underscore sync route can refresh SAP as a side effect.
DROP = {"/sap_sync/open-grpos/"}
REQ = {
    "status",
    "item_code",
    "year",
    "monthId",
    "license_no",
    "startDate",
    "endDate",
    "cardCode",
    "file_no",
}


def opid(p):
    return "get_" + re.sub(r"[{}]", "", p).strip("/").replace("/", "_").replace(
        "-", "_"
    )


paths = {}
for e in eps:
    p = e["path"]
    if p in DROP:
        continue
    item = paths.setdefault(p, {})
    params = []
    for pp in e.get("path_params", []):
        params.append(
            {
                "name": pp,
                "in": "path",
                "required": True,
                "schema": {"type": "string"},
                "description": f"{pp} identifier",
            }
        )
    for q in e.get("query_params", []):
        params.append(
            {
                "name": q,
                "in": "query",
                "required": q in REQ,
                "schema": {"type": "string"},
                "description": f"{q} filter",
            }
        )
    sample = e.get("response_sample")
    schema = (
        {"type": "array", "items": {"type": "object"}}
        if isinstance(sample, list)
        else {"type": "object"}
    )
    resp = {
        "200": {
            "description": "OK",
            "content": {"application/json": {"schema": schema}},
        }
    }
    if sample is not None:
        resp["200"]["content"]["application/json"]["example"] = sample
    item["get"] = {
        "operationId": opid(p),
        "summary": (e.get("desc") or p)[:120],
        "tags": [e["category"]],
        "parameters": params,
        "responses": resp,
    }
o = {
    "openapi": "3.0.3",
    "info": {
        "title": "JIVO EXIM",
        "version": "1.3.0",
        "description": "JIVO EXIM read-only surface. Write and sync-import endpoints are excluded.",
    },
    "servers": [{"url": "https://eximbe.jivo.in"}],
    "security": [{"bearerAuth": []}],
    "components": {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "x-auth-env-vars": ["EXIM_TOKEN"],
            }
        }
    },
    "paths": paths,
}
json.dump(o, open(f"{ROOT}/cli/exim-openapi.json", "w"), indent=2)
print(f"OpenAPI: {sum(len(v) for v in paths.values())} operations")
