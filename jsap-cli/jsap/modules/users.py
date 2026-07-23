"""Users module — accounts, roles, states, branches, budgets, permissions.

READ-ONLY: GET only. Wraps the User Management read surface — the permission
catalogues (roles/states/branches/budgets/sub-budgets/approvals/varieties/
reports/departments) that feed the permission-granting screen, a user's granted
effective permissions, the unregistered-in-company user pool, and the full user
list (scraped from the server-rendered AllUsers page — no JSON list exists).

Docs: docs/jsap/UserManagement.md
"""

from __future__ import annotations

import html as _htmllib
import re

from .._reg import endpoint, group


def register(subparsers):
    g = group(
        subparsers, "users", "Users, roles, states, branches, budgets, permissions"
    )

    # -- granted / effective permissions for a user in this company --------
    endpoint(
        g,
        "perms",
        path="/api/Permission/GetUserEffectivePermissions",
        help="A user's effective module/permission rows in the company",
        params=[
            {
                "name": "userId",
                "type": int,
                "required": False,
                "help": "User id (default: configured user)",
            }
        ],
        handler=_perms,
    )

    # -- the full user list (only available as server-rendered HTML) -------
    endpoint(
        g,
        "list",
        path="/UserManagement/AllUsers",
        help="All registered users in the company "
        "(name, empId, type, department, status) — scraped from HTML",
        handler=_all_users,
    )

    # -- unregistered-in-company user pool ---------------------------------
    endpoint(
        g,
        "unregistered",
        path="/api/auth/getusernotregisterincompany",
        help="Users not yet registered in the selected company",
        company_param="company",
    )

    # -- permission-bundle catalogues (all ?company=) ----------------------
    endpoint(
        g,
        "roles",
        path="/api/auth/getroles",
        help="Role catalog for the selected company",
        company_param="company",
    )

    endpoint(
        g,
        "states",
        path="/api/auth/getstates",
        help="State/zone codes for the selected company",
        company_param="company",
    )

    endpoint(
        g,
        "branches",
        path="/api/auth/getbranches",
        help="Branches for the selected company (IDs differ per company)",
        company_param="company",
    )

    endpoint(
        g,
        "budgets",
        path="/api/auth/getbudgets",
        help="Budget heads for the selected company",
        company_param="company",
    )

    endpoint(
        g,
        "subbudgets",
        path="/api/auth/getSubBudgets",
        help="Sub-budgets for the selected company",
        company_param="company",
    )

    endpoint(
        g,
        "approvals",
        path="/api/auth/getapprovals",
        help="Approval types for the selected company",
        company_param="company",
    )

    endpoint(
        g,
        "varieties",
        path="/api/auth/getVarieties",
        help="Item sub-groups (varieties) for the selected company",
        company_param="company",
    )

    endpoint(
        g,
        "reports",
        path="/api/auth/getreports",
        help="Report catalog for the selected company",
        company_param="company",
    )

    endpoint(
        g,
        "departments",
        path="/api/auth/getdepartments",
        help="Department list (global; company param is ignored server-side)",
        company_param="company",
    )


def _perms(client, args):
    from ..config import CONFIG

    uid = getattr(args, "userId", None) or CONFIG.user_id
    return client.get(
        "/api/Permission/GetUserEffectivePermissions",
        {"UserId": uid, "CompanyId": client.company},
    )


_ROW_RE = re.compile(r'<tr class="user-row">(.*?)</tr>', re.S)
_TYPE_DEPT_RE = re.compile(
    r'user-empid">.*?</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>', re.S
)


def _clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s)
    return _htmllib.unescape(s).strip()


def _cell(block: str, cls: str):
    m = re.search(r'<td class="%s">(.*?)</td>' % cls, block, re.S)
    return _clean(m.group(1)) if m else None


def _all_users(client, args):
    """Scrape the server-rendered AllUsers page into structured rows.

    The page has no JSON list endpoint; the user table is rendered into HTML.
    Purely a READ — fetches the page and parses the `.user-row` rows.
    """
    html = client.get("/UserManagement/AllUsers")
    if not isinstance(html, str):
        return html  # unexpected (e.g. an error envelope) — pass through
    rows = []
    for block in _ROW_RE.findall(html):
        uid = re.search(r'data-userid="(\d+)"', block)
        td = _TYPE_DEPT_RE.search(block)
        rows.append(
            {
                "userId": int(uid.group(1)) if uid else None,
                "name": _cell(block, "user-name"),
                "empId": _cell(block, "user-empid") or None,
                "userType": _clean(td.group(1)) if td else None,
                "department": _clean(td.group(2)) if td else None,
                "status": "active" if "slider round green" in block else "locked",
            }
        )
    return rows
