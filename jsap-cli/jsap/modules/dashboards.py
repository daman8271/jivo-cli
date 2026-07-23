"""Dashboards module — DashboardWeb controller (IT / Task / Client / MoM / Budget).

READ-ONLY: GET reads only. Wraps every read endpoint on the six DashboardWeb
pages (IT Standards, Tasks, Client/IT-Projects, MoM, Budget/Avtar) plus the
shared effective-permissions lookup. The MoM/account/session write endpoints are
documented in docs/jsap/Dashboards.md but deliberately NOT wrapped here.

Notes on scoping (per the docs):
  - The `/api/Dashboard/*` endpoints take no companyId — they read the session
    (bootstrapped from --company), so no company_param is set on them.
  - The Budget endpoints scope by an explicit `branch` (OIL|BEVERAGE) query
    param, independent of session company, and return bare JSON arrays.
  - GetUserEffectivePermissions takes UserId + CompanyId; defaults to the
    configured user (68) and the global --company.

Docs: docs/jsap/Dashboards.md
"""

from __future__ import annotations

from .._reg import endpoint, group
from ..config import CONFIG

# Shared task-dashboard filter params (stats / status-distribution /
# employee-stats / trend / list all accept these, all optional, server-side).
_TASK_FILTERS = [
    {
        "name": "group_by",
        "type": str,
        "required": False,
        "help": "Grouping dimension: PROJECT|MODULE|STATUS|TASK",
    },
    {
        "name": "assignedto",
        "type": str,
        "required": False,
        "help": "Filter by assignee (employee id)",
    },
    {
        "name": "project",
        "type": str,
        "required": False,
        "help": "Filter by project name",
    },
    {
        "name": "status",
        "type": str,
        "required": False,
        "help": "Filter by status (In Progress|Completed Ahead|Completed|Pending)",
    },
    {
        "name": "priority",
        "type": str,
        "required": False,
        "help": "Filter by priority (Critical|High|Medium|Low)",
    },
    {"name": "search", "type": str, "required": False, "help": "Free-text search"},
    {
        "name": "startDate",
        "type": str,
        "required": False,
        "help": "Start date (YYYY-MM-DD)",
    },
    {
        "name": "endDate",
        "type": str,
        "required": False,
        "help": "End date (YYYY-MM-DD)",
    },
]


def register(subparsers):
    g = group(subparsers, "dashboards", "IT/Task/Client/MoM/Budget dashboards")

    # -- Shared: effective permissions ------------------------------------
    endpoint(
        g,
        "perms",
        path="/api/Permission/GetUserEffectivePermissions",
        help="Effective module/permission rows for a user in a company",
        params=[
            {
                "name": "userId",
                "type": int,
                "required": False,
                "help": f"User id (default {CONFIG.user_id})",
            }
        ],
        handler=_perms,
    )

    # -- IT Standards dashboard -------------------------------------------
    endpoint(
        g,
        "itsummary",
        path="/api/Dashboard/GetSummary",
        help="IT-standards priority/gap counts {p1,p2,p3,high,medium,low}",
    )

    endpoint(
        g,
        "itmaster",
        path="/api/Dashboard/GetMaster",
        help="Full IT-standards register rows",
        params=[
            {
                "name": "priority",
                "type": str,
                "required": False,
                "help": "Optional priority filter: P1|P2|P3",
            }
        ],
    )

    # -- Tasks dashboard --------------------------------------------------
    # /api/Dashboard/stats requires group_by server-side (400 without it), unlike
    # the other filter-sharing endpoints — so require it just for taskstats.
    _stats_filters = [
        dict(p, required=True) if p["name"] == "group_by" else p for p in _TASK_FILTERS
    ]
    endpoint(
        g,
        "taskstats",
        path="/api/Dashboard/stats",
        help="Task KPI row by group (--group-by PROJECT|MODULE|STATUS|TASK required)",
        params=_stats_filters,
    )

    endpoint(
        g,
        "taskstatus",
        path="/api/Dashboard/status-distribution",
        help="Task status distribution [{status,count}]",
        params=list(_TASK_FILTERS),
    )

    endpoint(
        g,
        "taskemployees",
        path="/api/Dashboard/employee-stats",
        help="Per-assignee task totals",
        params=list(_TASK_FILTERS),
    )

    endpoint(
        g,
        "tasktrend",
        path="/api/Dashboard/trend",
        help="Daily created/completed task series",
        params=[
            {
                "name": "days",
                "type": int,
                "required": False,
                "help": "Number of days back (page uses 7)",
            }
        ]
        + list(_TASK_FILTERS),
    )

    endpoint(
        g,
        "tasks",
        path="/api/Dashboard/list",
        help="Task rows for the tasks table",
        params=list(_TASK_FILTERS),
    )

    endpoint(
        g,
        "projects",
        path="/api/Dashboard/projects",
        help="Project-name list (for task filters)",
    )

    endpoint(
        g,
        "employees",
        path="/api/Dashboard/employees",
        help="Employee list {employeeId, employeeName}",
    )

    endpoint(
        g,
        "task",
        path="/api/Dashboard/details",
        help="Single task detail by id (404 JSON if not found)",
        params=[
            {
                "name": "taskId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "Task id to fetch",
            }
        ],
    )

    # -- Client / IT-Projects dashboard -----------------------------------
    endpoint(
        g,
        "clients",
        path="/api/Dashboard/GetDashboardMaster",
        help="Per-client project/module/progress/hours summary (+TOTAL)",
    )

    endpoint(
        g,
        "clientprojects",
        path="/api/Dashboard/GetDashboardByCompany",
        help="Projects of one client",
        params=[
            {
                "name": "clientName",
                "type": str,
                "required": True,
                "positional": True,
                "help": "Client name (e.g. JIVO)",
            }
        ],
    )

    endpoint(
        g,
        "projectmodules",
        path="/api/Dashboard/GetDashboardProject",
        help="Modules of one project",
        params=[
            {
                "name": "projectId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "Project id",
            }
        ],
    )

    # -- MoM dashboard ----------------------------------------------------
    endpoint(
        g,
        "mom",
        path="/api/Dashboard/GetAllMoM",
        help="All meeting-minutes (MoM) records",
    )

    # -- Budget (Avtar) dashboard — bare-array responses, branch-scoped ----
    endpoint(
        g,
        "ledgers",
        path="/api/Dashboard/GetUniqueAccounts",
        help="Unique ledger account names (optionally by branch)",
        params=[
            {
                "name": "branch",
                "type": str,
                "required": False,
                "help": "Branch filter: OIL|BEVERAGE (omit = all)",
            }
        ],
    )

    endpoint(
        g,
        "budgetheads",
        path="/api/Dashboard/GetUniqueBudgets",
        help="Unique budget heads (optionally by branch)",
        params=[
            {
                "name": "branch",
                "type": str,
                "required": False,
                "help": "Branch filter: OIL|BEVERAGE (omit = all)",
            }
        ],
    )

    endpoint(
        g,
        "budgetdata",
        path="/api/Dashboard/getBudgetDataByBranch",
        help="Full budget fact table by branch (heavy — filter locally)",
        params=[
            {
                "name": "branch",
                "type": str,
                "required": False,
                "help": "Branch filter: OIL|BEVERAGE (omit = all)",
            }
        ],
    )


def _perms(client, args):
    """Effective permissions, defaulting userId to the configured user and
    CompanyId to the global --company scope."""
    uid = getattr(args, "userId", None) or CONFIG.user_id
    return client.get(
        "/api/Permission/GetUserEffectivePermissions",
        {"UserId": uid, "CompanyId": client.company},
    )
