"""Auto-discovers every JSAP module command group in this package.

A module file just needs a top-level `register(subparsers)` function. Drop a new
file in here and it joins the CLI automatically. Order follows JSAP_ORDER so the
help listing reads like the app's own navigation.
"""

from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

# Preferred display order (mirrors the JSAP sidebar / JSAP_MAP index).
JSAP_ORDER = [
    "dashboards",
    "inventory",
    "documents",
    "users",
    "reports",
    "bpmaster",
    "qc",
    "tasks",
    "tickets",
    "hierarchy",
    "bills",
    "dochub",
    "meta",
]


def _discover() -> list[ModuleType]:
    found: dict[str, ModuleType] = {}
    for info in pkgutil.iter_modules(__path__):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{__name__}.{info.name}")
        if hasattr(mod, "register"):
            found[info.name] = mod
    ordered = [found[n] for n in JSAP_ORDER if n in found]
    ordered += [m for n, m in found.items() if n not in JSAP_ORDER]
    return ordered


ALL_MODULES = _discover()
