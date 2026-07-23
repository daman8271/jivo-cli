"""Output rendering for the JSAP CLI: JSON, compact tables, field selection."""

from __future__ import annotations

import json
import sys
from typing import Any


def _flatten(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def render(
    data: Any,
    *,
    as_json: bool = False,
    select: str | None = None,
    limit: int | None = None,
) -> None:
    """Render a read result to stdout.

    as_json : emit pretty JSON (default is a human table for lists of objects)
    select  : comma-separated field names to keep (applies to lists of dicts)
    limit   : cap the number of rows shown
    """
    if select and isinstance(data, list):
        fields = [f.strip() for f in select.split(",") if f.strip()]
        data = [
            {k: row.get(k) for k in fields} if isinstance(row, dict) else row
            for row in data
        ]

    if isinstance(data, list) and limit is not None:
        data = data[:limit]

    if as_json or not _is_table(data):
        json.dump(data, sys.stdout, indent=2, ensure_ascii=False, default=str)
        sys.stdout.write("\n")
        return

    _print_table(data)


def _is_table(data: Any) -> bool:
    return (
        isinstance(data, list)
        and len(data) > 0
        and all(isinstance(r, dict) for r in data)
    )


def _print_table(rows: list[dict]) -> None:
    cols: list[str] = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    widths = {c: len(c) for c in cols}
    cells: list[list[str]] = []
    for r in rows:
        row = [_flatten(r.get(c)) for c in cols]
        for i, c in enumerate(cols):
            widths[c] = min(max(widths[c], len(row[i])), 60)
        cells.append(row)

    def fmt(vals: list[str]) -> str:
        return "  ".join(v[: widths[c]].ljust(widths[c]) for v, c in zip(vals, cols))

    print(fmt(cols))
    print("  ".join("-" * widths[c] for c in cols))
    for row in cells:
        print(fmt(row))
    print(f"\n[{len(rows)} row(s)]", file=sys.stderr)
