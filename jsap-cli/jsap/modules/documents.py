"""Documents module — Document Management (Document Dispatch).

Physical-document courier tracking between JIVO branches and Head Office:
dispatcher bundle history, receiver pending/history queues, the user's rejected
queue, and the SAP source documents a bundle is built from (GRPO / PO / AP Draft /
Goods Return). READ-ONLY: GET only. Docs: docs/jsap/DocumentManagement.md
"""

from __future__ import annotations

from .._reg import endpoint, group
from ..config import CONFIG


def register(subparsers):
    g = group(
        subparsers,
        "documents",
        "Document dispatch/receive/rejected + source docs (PO/GRPO/GR/AP)",
    )

    # -- SAP source documents (open docs across BOTH HANA companies at once) --
    endpoint(
        g,
        "grpo",
        path="/api/DocumentDispatch/GetGRPO",
        help="Open GRPOs across both companies (SAP source docs, ~10k rows)",
    )

    endpoint(
        g,
        "po",
        path="/api/DocumentDispatch/GetPO",
        help="Open Purchase Orders across both companies",
    )

    endpoint(
        g,
        "apdraft",
        path="/api/DocumentDispatch/GetApDraft",
        help="Open AP Invoice drafts across both companies",
    )

    endpoint(
        g,
        "gr",
        path="/api/DocumentDispatch/GetGR",
        help="Open Goods Returns across both companies",
    )

    # -- dispatcher: bundle history + rejected-queue for a user --
    endpoint(
        g,
        "docs",
        path="/api/DocumentDispatch/GetUserDocuments",
        help="Dispatched-bundle history for a user (default: session user 68)",
        params=[
            {
                "name": "userId",
                "type": int,
                "positional": True,
                "help": "User id (default: configured session user 68)",
            }
        ],
        handler=_user_docs,
    )

    endpoint(
        g,
        "rejected",
        path="/api/DocumentDispatch/GetRejectedDataByUserId",
        help="User's rejected docs awaiting re-dispatch (default: session user 68)",
        params=[
            {
                "name": "userId",
                "type": int,
                "positional": True,
                "help": "User id (default: configured session user 68)",
            }
        ],
        handler=_rejected,
    )

    # -- receiver: pending queue + full action history (company-scoped) --
    endpoint(
        g,
        "pending",
        path="/api/DocumentDispatch/GetRecieverPendingData",
        help="Receiver pending queue for the selected company (status S)",
        params=[
            {
                "name": "status",
                "type": str,
                "default": "S",
                "help": "Status filter (default S = pending)",
            }
        ],
        company_param="company",
    )

    endpoint(
        g,
        "history",
        path="/api/DocumentDispatch/GetRecieverActionData",
        help="Full receiver action/receive history for the selected company",
        company_param="company",
    )

    # -- bundle counter — READ ONLY: mode is hardcoded to `select` --
    endpoint(
        g,
        "bundleid",
        path="/api/DocumentDispatch/GetLastBundleId",
        help="Current bundle counter (mode=select, read-only)",
        handler=_last_bundle_id,
    )

    # -- attachment file streams --
    endpoint(
        g,
        "sapfile",
        path="/api/DocumentDispatch/SapDownloadFile",
        help="SAP attachment file stream by fileName (company-scoped)",
        params=[
            {
                "name": "fileName",
                "type": str,
                "required": True,
                "positional": True,
                "help": "SAP attachment file name (from a grpo/po `link` field)",
            }
        ],
        company_param="company",
    )

    endpoint(
        g,
        "file",
        path="/api/DocumentDispatch/DownloadFile",
        help="Uploaded-attachment file stream by stored filePath",
        params=[
            {
                "name": "filePath",
                "type": str,
                "required": True,
                "positional": True,
                "help": "Stored attachment path",
            }
        ],
    )


def _user_docs(client, args):
    uid = getattr(args, "userId", None) or CONFIG.user_id
    return client.get("/api/DocumentDispatch/GetUserDocuments", {"userId": uid})


def _rejected(client, args):
    uid = getattr(args, "userId", None) or CONFIG.user_id
    return client.get("/api/DocumentDispatch/GetRejectedDataByUserId", {"userId": uid})


def _last_bundle_id(client, args):
    # READ-ONLY: `mode` is fixed to `select`. The `mode=update` variant mutates
    # the counter and is deliberately unreachable from this CLI.
    return client.get("/api/DocumentDispatch/GetLastBundleId", {"mode": "select"})
