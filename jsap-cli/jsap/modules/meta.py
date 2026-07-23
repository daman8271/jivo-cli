"""Platform & cross-cutting reads: identity, companies, departments, permissions.

Reference module — hand-authored to establish the pattern. READ-ONLY: GET only.
Docs: docs/jsap/PlatformMeta.md
"""

from __future__ import annotations

from .._reg import endpoint, group


def register(subparsers):
    g = group(
        subparsers, "meta", "Platform meta: companies, departments, permissions, whoami"
    )

    endpoint(
        g,
        "companies",
        path="/api/auth/getcompanies",
        help="Companies this user belongs to",
        params=[
            {
                "name": "userId",
                "type": int,
                "required": False,
                "help": "User id (default: configured user)",
            }
        ],
        handler=lambda c, a: c.get(
            "/api/auth/getcompanies",
            {"userId": getattr(a, "userId", None) or __user(c)},
        ),
    )

    endpoint(
        g,
        "departments",
        path="/api/auth/getdepartments",
        help="Departments for the selected company",
        company_param="company",
    )

    endpoint(
        g,
        "permissions",
        path="/api/Permission/GetUserEffectivePermissions",
        help="Effective module/permission rows for a user in the company",
        params=[
            {
                "name": "UserId",
                "type": int,
                "required": False,
                "help": "User id (default: configured user)",
            }
        ],
        handler=lambda c, a: c.get(
            "/api/Permission/GetUserEffectivePermissions",
            {"UserId": getattr(a, "UserId", None) or __user(c), "CompanyId": c.company},
        ),
    )

    endpoint(
        g,
        "whoami",
        path="/api/auth/getcompanies",
        help="Show the configured identity and company scope",
        handler=_whoami,
    )


def __user(client) -> int:
    from ..config import CONFIG

    return CONFIG.user_id


def _whoami(client, args):
    from ..config import CONFIG

    return {
        "userId": CONFIG.user_id,
        "userName": CONFIG.username,
        "company": client.company,
        "companyName": CONFIG.companies.get(client.company),
        "baseUrl": CONFIG.base_url,
        "companies": CONFIG.companies,
    }
