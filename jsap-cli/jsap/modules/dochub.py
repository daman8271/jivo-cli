"""Document Hub module — folder/file explorer + backup/recovery reads.

READ-ONLY: GET only. Document Hub is company-agnostic — none of its endpoints
take a companyId (the same tree is returned regardless of selected company);
only the shared-layout permissions endpoint is company-scoped. Docs:
docs/jsap/DocumentHub.md
"""

from __future__ import annotations

from .._reg import endpoint, group
from ..config import CONFIG


def register(subparsers):
    g = group(subparsers, "dochub", "Document Hub folder/backup reads")

    endpoint(
        g,
        "hub",
        path="/DocumentHub/GetHub",
        help="Directory listing: folders, files, breadcrumb, stats, perms",
        params=[
            {
                "name": "folderId",
                "type": int,
                "required": False,
                "positional": True,
                "help": "Folder id to list (omit for root)",
            },
            {
                "name": "filter",
                "type": str,
                "required": False,
                "help": "View filter: '' (all) | recent | trash",
            },
            {
                "name": "search",
                "type": str,
                "required": False,
                "help": "Search text (matches file/folder names)",
            },
        ],
    )

    endpoint(
        g,
        "folders",
        path="/DocumentHub/GetFolders",
        help="Flat list of ALL folders (build tree via parentFolderId)",
    )

    endpoint(
        g,
        "file",
        path="/DocumentHub/FileAccessInfo",
        help="File metadata + isConfidential/accessGranted flags",
        params=[
            {
                "name": "fileId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "File id",
            }
        ],
    )

    endpoint(
        g,
        "versions",
        path="/DocumentHub/VersionHistory",
        help="Stored version history for a file",
        params=[
            {
                "name": "fileId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "File id",
            }
        ],
    )

    endpoint(
        g,
        "activity",
        path="/DocumentHub/ActivityLog",
        help="Audit trail (view/upload/...) for a file",
        params=[
            {
                "name": "fileId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "File id",
            }
        ],
    )

    endpoint(
        g,
        "backups",
        path="/DocumentHub/GetBackups",
        help="Backup snapshot list (Full/Incremental)",
    )

    endpoint(
        g,
        "backup",
        path="/DocumentHub/GetBackupContent",
        help="Snapshot manifest: folders, files, versions, activities",
        params=[
            {
                "name": "backupId",
                "type": str,
                "required": True,
                "positional": True,
                "help": "Backup id, e.g. DH-20260710110815",
            }
        ],
    )

    endpoint(
        g,
        "preview",
        path="/DocumentHub/Preview",
        help="Raw file bytes served inline (Content-Disposition: inline)",
        params=[
            {
                "name": "fileId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "File id",
            }
        ],
    )

    endpoint(
        g,
        "download",
        path="/DocumentHub/Download",
        help="Raw file bytes (read-with-side-log: server may log a Download)",
        params=[
            {
                "name": "fileId",
                "type": int,
                "required": True,
                "positional": True,
                "help": "File id",
            }
        ],
    )

    endpoint(
        g,
        "perms",
        path="/api/Permission/GetUserEffectivePermissions",
        help="Shared-layout effective module permissions (company-scoped)",
        params=[
            {
                "name": "userId",
                "type": int,
                "required": False,
                "help": "User id (defaults to the configured user)",
            }
        ],
        handler=_perms,
    )


def _perms(client, args):
    uid = getattr(args, "userId", None)
    if uid is None:
        uid = CONFIG.user_id
    return client.get(
        "/api/Permission/GetUserEffectivePermissions",
        {"UserId": uid, "CompanyId": client.company},
    )
