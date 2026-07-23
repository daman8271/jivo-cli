"""Declarative endpoint registration helpers.

Module files describe their read endpoints as data; this module turns each into
an argparse subcommand whose handler performs a single authenticated GET. Keeps
every module file uniform (easy to write, easy to audit for read-only safety).

A param spec is a dict:
    {"name": "month", "type": str, "required": True, "help": "...",
     "positional": False, "default": None, "path": False, "company": False}
Shorthand tuples are also accepted: (name, type, required, help).
"""

from __future__ import annotations

import argparse
from typing import Any, Callable

# Shared parent parser carrying the global/render flags so they are accepted
# AFTER the subcommand too (argparse only honours root-level flags before the
# subcommand otherwise). cli.py installs it via set_common() before registering.
_COMMON: argparse.ArgumentParser | None = None


def set_common(parser: argparse.ArgumentParser) -> None:
    global _COMMON
    _COMMON = parser


def group(subparsers, name: str, help: str):
    p = subparsers.add_parser(name, help=help, description=help)
    sub = p.add_subparsers(dest="_cmd", metavar="<command>")
    sub.required = True
    p.set_defaults(_group=name)
    return sub


def _norm(spec) -> dict:
    if isinstance(spec, dict):
        d = dict(spec)
    else:  # tuple shorthand
        name, typ, required, help = (list(spec) + [None] * 4)[:4]
        d = {"name": name, "type": typ, "required": required, "help": help}
    d.setdefault("type", str)
    d.setdefault("required", False)
    d.setdefault("help", "")
    d.setdefault("positional", False)
    d.setdefault("default", None)
    d.setdefault("path", False)  # substitutes into {name} in the URL path
    d.setdefault("company", False)  # auto-filled from --company
    return d


def endpoint(
    sub,
    name: str,
    *,
    path: str,
    help: str,
    params: list | None = None,
    unwrap: bool = True,
    handler: Callable | None = None,
    company_param: str | None = None,
    method: str = "GET",
):
    """Register one read endpoint as a subcommand.

    path         : URL path, may contain {placeholders} filled by path params
    params       : list of param specs (dicts or (name,type,required,help) tuples)
    unwrap       : return the {success,data} `data` payload (default True)
    handler      : optional custom callable(client, args) -> data for complex cases
    company_param: if set, the client's --company value is sent as this key.
                   For GET it's a query param; for POST it's a body field.
    method       : "GET" (default) or "POST" for POST-to-read endpoints. POST
                   sends non-path params in the JSON body via client.read_post,
                   which refuses any non-read leaf verb (READ-ONLY LAW).
    """
    specs = [_norm(s) for s in (params or [])]
    parents = [_COMMON] if _COMMON is not None else []
    p = sub.add_parser(name, help=help, description=help, parents=parents)
    for s in specs:
        if s["company"]:
            continue  # value comes from the global --company, no leaf flag
        typ = s["type"]
        if s["positional"]:
            p.add_argument(
                s["name"],
                type=typ,
                help=s["help"],
                nargs=None if s["required"] else "?",
                default=s["default"],
            )
        else:
            argname = "--" + s["name"].replace("_", "-")
            p.add_argument(
                argname,
                dest=s["name"],
                type=typ,
                required=s["required"],
                default=s["default"],
                help=s["help"],
                metavar=s["name"].upper(),
            )

    is_post = method.upper() == "POST"

    def _run(client, args) -> Any:
        if handler is not None:
            return handler(client, args)
        url = path
        payload: dict[str, Any] = {}
        for s in specs:
            val = getattr(args, s["name"], None)
            if s["path"]:
                url = url.replace(
                    "{" + s["name"] + "}", "" if val is None else str(val)
                )
            elif s["company"]:
                payload[s["name"]] = client.company
            elif val is not None:
                payload[s["name"]] = val
        if company_param:
            payload[company_param] = client.company
        if is_post:
            return client.read_post(url, payload, unwrap=unwrap)
        return client.get(url, payload, unwrap=unwrap)

    p.set_defaults(_run=_run)
    return p
