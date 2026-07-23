"""Tickets module — IT-helpdesk / support-ticket reads.

READ-ONLY: wraps only the pure-read surface of /api/Tickets (see
docs/jsap/Tickets.md). No ticket lifecycle, assignment, comment, or attachment
WRITE is ever wrapped here.

API convention (from the docs): almost every Tickets *read* is served over POST
with a JSON filter body but is a pure `Get*` read; only GetUsersForAssignment
and DownloadAttachment/{id} are true GETs. The POST-reads go through
client.read_post, which refuses any non-read leaf verb. Ticket data is global
across both companies — no endpoint takes a company param.
"""

from __future__ import annotations

from .._reg import endpoint, group
from ..config import CONFIG


def register(subparsers):
    g = group(subparsers, "tickets", "Raise/My/Assigned/Admin ticket reads")

    endpoint(
        g,
        "projects",
        method="POST",
        path="/api/Tickets/GetAllProjects",
        help="Ticket projects with per-project ticket counts",
        params=[
            {
                "name": "includeInactive",
                "type": bool,
                "required": False,
                "help": "Include inactive projects (default: active only)",
            }
        ],
    )

    endpoint(
        g,
        "mine",
        method="POST",
        path="/api/Tickets/GetMyTickets",
        help="Tickets raised by a user (default: configured user)",
        params=[
            {
                "name": "userId",
                "type": int,
                "required": False,
                "help": "Requester user id (default: configured user)",
            },
            {
                "name": "status",
                "type": str,
                "required": False,
                "help": "Open / Assign / InProgress / OnHold / Close",
            },
            {
                "name": "projectId",
                "type": int,
                "required": False,
                "help": "Filter by project id",
            },
            {"name": "month", "type": int, "required": False, "help": "Month 1-12"},
            {"name": "year", "type": int, "required": False, "help": "Year"},
        ],
        handler=_mine,
    )

    endpoint(
        g,
        "all",
        method="POST",
        path="/api/Tickets/GetAllTickets",
        help="Every ticket across all users (admin view)",
        params=[
            {
                "name": "status",
                "type": str,
                "required": False,
                "help": "Open / Assign / InProgress / OnHold / Close",
            },
            {
                "name": "projectId",
                "type": int,
                "required": False,
                "help": "Filter by project id",
            },
            {
                "name": "priority",
                "type": str,
                "required": False,
                "help": "Low / Medium / High / Critical",
            },
            {"name": "month", "type": int, "required": False, "help": "Month 1-12"},
            {"name": "year", "type": int, "required": False, "help": "Year"},
        ],
    )

    endpoint(
        g,
        "assigned",
        method="POST",
        path="/api/Tickets/GetAssignedTickets",
        help="Tickets assigned to a user (default: configured user)",
        params=[
            {
                "name": "assigneeUserId",
                "type": int,
                "required": False,
                "help": "Assignee user id (default: configured user)",
            },
            {
                "name": "status",
                "type": str,
                "required": False,
                "help": "Assign / InProgress / OnHold / Close",
            },
            {
                "name": "projectId",
                "type": int,
                "required": False,
                "help": "Filter by project id",
            },
            {"name": "month", "type": int, "required": False, "help": "Month 1-12"},
            {"name": "year", "type": int, "required": False, "help": "Year"},
        ],
        handler=_assigned,
    )

    endpoint(
        g,
        "ticket",
        method="POST",
        path="/api/Tickets/GetTicketById",
        help="Full single ticket incl. requester name/email",
        params=[
            {
                "name": "ticketId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "Ticket id",
            }
        ],
    )

    endpoint(
        g,
        "timeline",
        method="POST",
        path="/api/Tickets/GetTicketTimeline",
        help="Activity history for one ticket (action, old/new, user, time)",
        params=[
            {
                "name": "ticketId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "Ticket id",
            }
        ],
    )

    endpoint(
        g,
        "attachments",
        method="POST",
        path="/api/Tickets/GetAttachmentsByTicketId",
        help="Attachment metadata rows for one ticket",
        params=[
            {
                "name": "ticketId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "Ticket id",
            }
        ],
    )

    endpoint(
        g,
        "comments",
        method="POST",
        path="/api/Tickets/GetCommentsByTicketId",
        help="Comment rows for one ticket (internal notes included by default)",
        params=[
            {
                "name": "ticketId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "Ticket id",
            },
            {
                "name": "includeInternal",
                "type": bool,
                "required": False,
                "help": "Include internal-only notes (default: yes)",
            },
        ],
        handler=_comments,
    )

    endpoint(
        g,
        "workload",
        method="POST",
        path="/api/Tickets/GetMyWorkloadSummary",
        help="Status-count workload summary for an assignee",
        params=[
            {
                "name": "assigneeUserId",
                "type": int,
                "required": False,
                "help": "Assignee user id (default: configured user)",
            }
        ],
        handler=_workload,
    )

    # -- the two true GETs --
    endpoint(
        g,
        "users",
        path="/api/Tickets/GetUsersForAssignment",
        help="Assignable users with their active-ticket counts",
    )

    endpoint(
        g,
        "download",
        path="/api/Tickets/DownloadAttachment/{attachmentId}",
        help="Download one attachment by id (binary file stream)",
        params=[
            {
                "name": "attachmentId",
                "type": int,
                "required": True,
                "positional": True,
                "path": True,
                "help": "Attachment id",
            }
        ],
    )


def _add(body, args, *names):
    for n in names:
        v = getattr(args, n, None)
        if v is not None:
            body[n] = v


def _mine(client, args):
    b = {"userId": getattr(args, "userId", None) or CONFIG.user_id}
    _add(b, args, "status", "projectId", "month", "year")
    return client.read_post("/api/Tickets/GetMyTickets", b)


def _assigned(client, args):
    b = {"assigneeUserId": getattr(args, "assigneeUserId", None) or CONFIG.user_id}
    _add(b, args, "status", "projectId", "month", "year")
    return client.read_post("/api/Tickets/GetAssignedTickets", b)


def _comments(client, args):
    inc = getattr(args, "includeInternal", None)
    inc = True if inc is None else bool(inc)
    return client.read_post(
        "/api/Tickets/GetCommentsByTicketId",
        {"ticketId": args.ticketId, "includeInternal": inc},
    )


def _workload(client, args):
    uid = getattr(args, "assigneeUserId", None) or CONFIG.user_id
    # Backend can return 200 + success:false ("DBNull" bug) when the user has no
    # assigned tickets; return the full envelope so the message stays visible.
    return client.read_post(
        "/api/Tickets/GetMyWorkloadSummary", {"assigneeUserId": uid}, unwrap=False
    )
