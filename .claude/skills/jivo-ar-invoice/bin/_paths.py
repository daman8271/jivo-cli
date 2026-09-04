"""Repo and binary resolution that works on the Mac AND on an operator's Windows box.

Never hard-code a path: the Mac has sap-b1/cli/sapb1 and hana-sql/hana-sql, a
Windows operator box has the .exe forms, and the checkout lives somewhere else
entirely (C:/Users/<user>/Documents/jivo-cli). Walk up from this file instead.
"""
import os
import pathlib
import sys


def find_repo():
    here = pathlib.Path(__file__).resolve()
    for p in [here] + list(here.parents):
        if (p / "sap-b1").is_dir() and (p / "harness").is_dir():
            return p
    sys.exit("jivo-ar-invoice: cannot find the jivo-cli checkout above " + str(here))


REPO = pathlib.Path(os.environ.get("JIVO_REPO") or find_repo())


def _first(*rel):
    for r in rel:
        p = REPO / r
        if p.exists():
            return str(p)
    return None


WINDOWS = os.name == "nt"


def sapb1():
    # both binaries are committed, so the PLATFORM decides - not which file exists.
    cands = (("sap-b1/cli/sapb1.exe", "sap-b1/accounts-kit/sapb1.exe")
             if WINDOWS else ("sap-b1/cli/sapb1",))
    p = _first(*cands)
    if not p:
        sys.exit("jivo-ar-invoice: no sapb1 binary for this platform under "
                 + str(REPO / "sap-b1"))
    return p


def hana_sql():
    cands = ("hana-sql/hana-sql.exe",) if WINDOWS else ("hana-sql/hana-sql",)
    p = _first(*cands)
    if not p:
        sys.exit("jivo-ar-invoice: no hana-sql binary for this platform under "
                 + str(REPO / "hana-sql"))
    return p


def env_file(company):
    """The USER19 login for one book. Boxes name these slightly differently."""
    stem = {"JIVO_OIL_HANADB": "oil", "JIVO_MART_HANADB": "mart",
            "JIVO_BEVERAGES_HANADB": "bev"}.get(company)
    if not stem:
        sys.exit("jivo-ar-invoice: unknown company " + str(company))
    p = _first(f"sap-b1/cli/user19-{stem}.env",
               f"sap-b1/cli/mahak-user19-{stem}.env",
               f"sap-b1/cli/user19{'' if stem == 'oil' else '-' + stem}.env")
    if not p:
        sys.exit(f"jivo-ar-invoice: no USER19 login file for {company} under "
                 f"{REPO / 'sap-b1' / 'cli'} — expected user19-{stem}.env")
    return p


def load_env(company):
    env = dict(os.environ)
    with open(env_file(company)) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k] = v
    return env
