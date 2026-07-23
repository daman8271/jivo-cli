"""Tasks module — Task Manager (Daily Task) read surface.

READ-ONLY. Wraps the GET reads plus the two POST-to-read data endpoints
(`GetAllTasks`, `GetDashboard`) that power the task list and stat cards — these
are pure reads served over POST, routed through client.read_post (which refuses
any non-read leaf verb). Task API scoping is by employee hierarchy, so most
endpoints take no company param — except the shared permission check (CompanyId).
Docs: docs/jsap/TaskManager.md
"""

from __future__ import annotations

from .._reg import endpoint, group
from ..config import CONFIG


def register(subparsers):
    g = group(subparsers, "tasks", "Tasks & task dashboards")

    # -- the core POST-to-read data endpoints --
    endpoint(
        g,
        "list",
        method="POST",
        path="/api/Task/GetAllTasks",
        help="Task list (paged, filterable). Defaults: viewMode=ALL, this user",
        params=[
            {
                "name": "employeeId",
                "type": int,
                "required": False,
                "help": f"Task-system employee id (default {CONFIG.user_id}, the "
                "account user id — may differ from your app employee id; "
                "pass --employeeId to scope to a specific employee)",
            },
            {
                "name": "roleTypeId",
                "type": int,
                "required": False,
                "help": "Role type id (default 1)",
            },
            {
                "name": "viewMode",
                "type": str,
                "required": False,
                "help": "OWN | TEAM | ALL (default ALL)",
            },
            {
                "name": "status",
                "type": str,
                "required": False,
                "help": "PENDING|SUBMITTED|IN_PROGRESS|COMPLETED|NOT_STARTED",
            },
            {
                "name": "priority",
                "type": str,
                "required": False,
                "help": "LOW|MEDIUM|HIGH|CRITICAL",
            },
            {
                "name": "taskType",
                "type": str,
                "required": False,
                "help": "SELF | ASSIGNED",
            },
            {
                "name": "assignedToEmployeeId",
                "type": int,
                "required": False,
                "help": "Filter to tasks assigned to this employee id",
            },
            {
                "name": "page",
                "type": int,
                "required": False,
                "help": "Page (default 1)",
            },
            {
                "name": "page_size",
                "type": int,
                "required": False,
                "help": "Rows per page in the request body (default 50)",
            },
        ],
        handler=_list,
    )

    endpoint(
        g,
        "dashboard",
        method="POST",
        path="/api/Task/GetDashboard",
        help="Task stat cards: my/team totals + per-member breakdown",
        params=[
            {
                "name": "employeeId",
                "type": int,
                "required": False,
                "help": f"Task-system employee id (default {CONFIG.user_id}, the "
                "account user id — may differ from your app employee id; "
                "pass --employeeId to scope to a specific employee)",
            },
            {
                "name": "roleTypeId",
                "type": int,
                "required": False,
                "help": "Role type id (default 1)",
            },
        ],
        handler=_dashboard,
    )

    # -- GET reads --
    endpoint(
        g,
        "team",
        path="/TaskWeb/GetTeamMembers",
        help="Team member roster (id/name/code/designation/role/roleTypeId)",
        params=[
            {
                "name": "scope",
                "type": str,
                "required": False,
                "help": "Optional scope, e.g. 'allhods' for the HOD list "
                "(needs HOD-assign rights server-side)",
            },
        ],
    )

    endpoint(
        g,
        "tree",
        path="/TaskWeb/GetHierarchyTree",
        help="HOD department -> subHods -> executives hierarchy tree with counts",
    )

    endpoint(
        g,
        "details",
        path="/api/Task/GetTaskDetails/{taskId}",
        help="Full single-task record for a taskId (404 JSON when not found)",
        params=[
            {
                "name": "taskId",
                "type": str,
                "required": True,
                "positional": True,
                "path": True,
                "help": "Task id (string)",
            },
        ],
    )

    endpoint(
        g,
        "progress",
        path="/api/Task/GetProgressUpdates/{taskId}",
        help="Progress-update log rows for a taskId "
        "(employeeName/updateDate/percentComplete/updateText)",
        params=[
            {
                "name": "taskId",
                "type": str,
                "required": True,
                "positional": True,
                "path": True,
                "help": "Task id (string)",
            },
        ],
    )

    endpoint(
        g,
        "permissions",
        path="/api/Permission/GetUserEffectivePermissions",
        help="Effective module permissions for a user in the selected company "
        "(detects whether Task Manager is available)",
        params=[
            {
                "name": "userId",
                "type": int,
                "required": False,
                "help": "User id to check (defaults to the configured CLI user)",
            },
        ],
        handler=_permissions,
    )


def _list(client, args):
    b = {
        "employeeId": getattr(args, "employeeId", None) or CONFIG.user_id,
        "roleTypeId": getattr(args, "roleTypeId", None) or 1,
        "viewMode": getattr(args, "viewMode", None) or "ALL",
        "page": getattr(args, "page", None) or 1,
        "limit": getattr(args, "page_size", None) or 50,
        "sortBy": "created_on",
        "sortOrder": "DESC",
    }
    for opt in ("status", "priority", "taskType", "assignedToEmployeeId"):
        v = getattr(args, opt, None)
        if v is not None:
            b[opt] = v
    return client.read_post("/api/Task/GetAllTasks", b)


def _dashboard(client, args):
    return client.read_post(
        "/api/Task/GetDashboard",
        {
            "employeeId": getattr(args, "employeeId", None) or CONFIG.user_id,
            "roleTypeId": getattr(args, "roleTypeId", None) or 1,
        },
    )


def _permissions(client, args):
    """UserId defaults to the CLI's configured user; company scopes via CompanyId."""
    uid = getattr(args, "userId", None) or CONFIG.user_id
    return client.get(
        "/api/Permission/GetUserEffectivePermissions",
        {"UserId": uid, "CompanyId": client.company},
    )
