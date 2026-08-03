#!/usr/bin/env python3
"""Parse the shipped v0.1.0 spec into structured metadata.

The regenerated spec CARRIES FORWARD every shipped description, parameter and
enum by default, and lets a domain study overlay improvements on top. That
ordering matters: twenty parallel agents will each miss something, and an
operator whose parameter documentation silently got thinner cannot tell whether
it was deliberate. Regeneration must never lose metadata it already had.

Emits: {normalised_path: {resource, command, description, params[], response_type}}
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "harvest"))
from normalise import norm  # noqa: E402

SPEC = "/Users/damanpreetsingh/jivo-cli/ecom-cli/spec.yaml"


def parse():
    lines = open(SPEC).read().split("\n")
    out = {}
    res = ep = None
    cur = None
    param = None
    in_params = in_enum = False
    for raw in lines:
        if not raw.strip():
            continue
        indent = len(raw) - len(raw.lstrip())
        s = raw.strip()

        m = re.match(r"^([\w\-]+):$", s)
        if m and indent == 2:
            res = m.group(1); ep = None; cur = None
            in_params = in_enum = False
            continue
        if m and indent == 6:
            ep = m.group(1)
            cur = {"resource": res, "command": ep, "description": "",
                   "params": [], "response_type": "object", "path": None,
                   "placeholders": [], "method": "GET"}
            param = None
            in_params = in_enum = False
            continue
        if cur is None:
            continue

        # A params list item sits at the SAME indent as the `params:` key that
        # owns it, so this must be tested before the generic indent-8 branch -
        # otherwise every parameter is swallowed and the spec regenerates with
        # zero documented params while looking perfectly well-formed.
        if in_params and indent == 8 and s.startswith("- name:"):
            param = {"name": s.split(":", 1)[1].strip().strip("'\""),
                     "type": "string", "description": "", "enum": [],
                     "required": False}
            cur["params"].append(param)
            in_enum = False
            continue

        if indent == 8:
            in_params = in_enum = False
            if s.startswith("path:"):
                cur["path"] = s.split(":", 1)[1].strip()
                # The press substitutes path placeholders BY NAME, matching them
                # against the declared params. The shipped spec uses named
                # placeholders (`/api/dashboard/table-count/{table}`); emitting an
                # anonymous `{}` silently disables substitution and the CLI sends
                # the literal brace to the server. Keep the shipped names - they
                # are also the operator-facing flag names.
                cur["placeholders"] = re.findall(r"\{([^{}]+)\}", cur["path"])
            elif s.startswith("method:"):
                cur["method"] = s.split(":", 1)[1].strip()
            elif s.startswith("description:"):
                cur["description"] = s.split(":", 1)[1].strip().strip("'\"")
            elif s.startswith("params:"):
                in_params = True
            elif s.startswith("response:"):
                pass
            if cur["path"]:
                out[norm(cur["path"])] = cur
            continue

        if s.startswith("type:") and not in_params:
            cur["response_type"] = s.split(":", 1)[1].strip()
            continue

        if in_params:
            if s.startswith("- name:"):
                param = {"name": s.split(":", 1)[1].strip().strip("'\""),
                         "type": "string", "description": "", "enum": [],
                         "required": False}
                cur["params"].append(param)
                in_enum = False
            elif param is not None:
                if s.startswith("type:"):
                    param["type"] = s.split(":", 1)[1].strip()
                    in_enum = False
                elif s.startswith("description:"):
                    param["description"] = s.split(":", 1)[1].strip().strip("'\"")
                    in_enum = False
                elif s.startswith("required:"):
                    param["required"] = s.split(":", 1)[1].strip() == "true"
                    in_enum = False
                elif s.startswith("enum:"):
                    in_enum = True
                elif in_enum and s.startswith("- "):
                    param["enum"].append(s[2:].strip().strip("'\""))
    return out


if __name__ == "__main__":
    meta = parse()
    json.dump(meta, open(os.path.join(HERE, "old-spec-meta.json"), "w"), indent=1)
    withdesc = sum(1 for v in meta.values() if v["description"])
    withparams = sum(1 for v in meta.values() if v["params"])
    enums = sum(len(p["enum"]) for v in meta.values() for p in v["params"])
    print(f"parsed {len(meta)} endpoints")
    print(f"  with description: {withdesc}")
    print(f"  with params:      {withparams}")
    print(f"  total params:     {sum(len(v['params']) for v in meta.values())}")
    print(f"  total enum values:{enums}")
    import collections
    print("  response types:", collections.Counter(v["response_type"] for v in meta.values()))
    miss = [p for p, v in meta.items() if not v["description"]]
    if miss:
        print("  MISSING description:", miss[:10])
