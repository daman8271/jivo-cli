"""Reports module — Approval Status / Budget Approval report.

Reference module — hand-authored to establish the pattern. READ-ONLY: GET only.
This is nirmalkaur's primary access. Docs: docs/jsap/Reports.md
"""

from __future__ import annotations

from .._reg import endpoint, group


def register(subparsers):
    g = group(subparsers, "reports", "Approval Status / Budget Approval report")

    endpoint(
        g,
        "insight",
        path="/api/auth/GetAllBudgetInsight",
        help="Per-user Pending/Approved/Rejected budget counts for a month",
        params=[
            {
                "name": "month",
                "type": str,
                "required": True,
                "help": "Month as MM-YYYY, e.g. 06-2026",
            },
        ],
        company_param="company",
    )

    endpoint(
        g,
        "summary",
        path="/api/auth/GetAllBudgetSummaryAmount",
        help="Full nested budget summary export dataset for a month",
        params=[
            {"name": "month", "type": str, "required": True, "help": "Month as MM-YYYY"}
        ],
        company_param="company",
    )

    endpoint(
        g,
        "lookup",
        path="/api/Reports/GetBudgetByCompany",
        help="Look up budget docs by DocEntry (numeric) or CardName (text)",
        params=[
            {
                "name": "month",
                "type": str,
                "required": False,
                "help": "Month as MM-YYYY (ignored for docEntry lookups)",
            },
            {
                "name": "docEntry",
                "type": int,
                "required": False,
                "help": "SAP DocEntry (numeric lookup)",
            },
            {
                "name": "cardName",
                "type": str,
                "required": False,
                "help": "Vendor CardName (exact full-name match, uppercased)",
            },
        ],
        handler=_lookup,
    )

    for status in ("pending", "approved", "rejected"):
        endpoint(
            g,
            status,
            path=f"/api/auth/get{status}budgetwithdetails",
            help=f"{status.capitalize()} budget documents for a user/month",
            params=[
                {
                    "name": "userId",
                    "type": int,
                    "required": True,
                    "help": "User id to drill into",
                },
                {
                    "name": "month",
                    "type": str,
                    "required": True,
                    "help": "Month as MM-YYYY",
                },
            ],
            company_param="company",
        )

    endpoint(
        g,
        "flow",
        path="/api/auth/GetBudgetApprovalFlow",
        help="Stage-by-stage approval flow for one budget document",
        params=[
            {
                "name": "budgetId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "Budget document id",
            }
        ],
    )


def _lookup(client, args):
    q = {"company": client.company}
    if getattr(args, "month", None):
        q["month"] = args.month
    if getattr(args, "docEntry", None) is not None:
        q["docEntry"] = args.docEntry
    elif getattr(args, "cardName", None):
        q["cardName"] = args.cardName.upper()
    else:
        raise SystemExit("provide --docEntry or --cardName")
    return client.get("/api/Reports/GetBudgetByCompany", q)
