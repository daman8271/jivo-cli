"""Inventory Audit module — physical stock-count audit sessions & reports.

READ-ONLY: GET only. Wraps every read endpoint in the Inventory Audit page set
(All Session / Add Session dropdown feeds / Assigned Session) plus the item-level
audit report. No write path (CreateSessionWithBulkStockCount et al.) is wrapped.
Docs: docs/jsap/InventoryAudit.md
"""

from __future__ import annotations

from .._reg import endpoint, group
from ..config import CONFIG


def register(subparsers):
    g = group(subparsers, "inventory", "Inventory audit sessions & reports")

    # -- Sessions assigned to a user (All Session page) --------------------
    endpoint(
        g,
        "active",
        path="/api/InventoryAudit/GetUserActiveSessions",
        help="Active audit sessions assigned to a user (data.sessions + summary)",
        params=[
            {
                "name": "userId",
                "type": int,
                "positional": True,
                "required": False,
                "default": CONFIG.user_id,
                "help": f"User id (default {CONFIG.user_id})",
            }
        ],
    )

    endpoint(
        g,
        "inactive",
        path="/api/InventoryAudit/GetUserInactiveSessions",
        help="Inactive/deactivated sessions assigned to a user (empty => success:false)",
        params=[
            {
                "name": "userId",
                "type": int,
                "positional": True,
                "required": False,
                "default": CONFIG.user_id,
                "help": f"User id (default {CONFIG.user_id})",
            }
        ],
    )

    # -- Sessions created by a user (Assigned Session page) ----------------
    endpoint(
        g,
        "created-active",
        path="/api/InventoryAudit/GetActiveSessionsByUser",
        help="Active audit sessions created by a user (flat data[])",
        params=[
            {
                "name": "createdBy",
                "type": int,
                "positional": True,
                "required": False,
                "default": CONFIG.user_id,
                "help": f"Creator user id (default {CONFIG.user_id})",
            }
        ],
    )

    endpoint(
        g,
        "created-inactive",
        path="/api/InventoryAudit/GetInActiveSessionsByUser",
        help="Inactive audit sessions created by a user (flat data[])",
        params=[
            {
                "name": "createdBy",
                "type": int,
                "positional": True,
                "required": False,
                "default": CONFIG.user_id,
                "help": f"Creator user id (default {CONFIG.user_id})",
            }
        ],
    )

    # -- The item-level audit report (star endpoint) ----------------------
    endpoint(
        g,
        "report",
        path="/api/InventoryAudit/DownloadInventoryReport",
        help="Item-level audit report (system vs physical qty/value/litre per item)",
        params=[
            {
                "name": "lotNumber",
                "type": str,
                "positional": True,
                "required": True,
                "help": "Lot number, e.g. KAMALPREET19",
            },
            {
                "name": "userId",
                "type": int,
                "required": False,
                "default": CONFIG.user_id,
                "help": f"User id (default {CONFIG.user_id})",
            },
        ],
    )

    # -- Add Session scope dropdown feeds ---------------------------------
    endpoint(
        g,
        "units",
        path="/api/InventoryAudit/GetUnits",
        help="Unit list for the active company",
        company_param="company",
    )

    endpoint(
        g,
        "locations",
        path="/api/InventoryAudit/GetLocation",
        help="Locations for a unit (Unit required)",
        params=[
            {
                "name": "Unit",
                "type": str,
                "positional": True,
                "required": True,
                "help": "Unit name, e.g. OIL",
            }
        ],
        company_param="company",
    )

    endpoint(
        g,
        "warehouses",
        path="/api/InventoryAudit/getwarehouse",
        help="Warehouses at a location",
        params=[
            {
                "name": "LocationCode",
                "type": str,
                "positional": True,
                "required": True,
                "help": "Location code, e.g. 1",
            }
        ],
        company_param="company",
    )

    endpoint(
        g,
        "groups",
        path="/api/ItemMaster/GetGroup",
        help="Item groups (code + name) for the active company",
        company_param="company",
    )

    endpoint(
        g,
        "subgroups",
        path="/api/InventoryAudit/GetSubGroups",
        help="Item sub-groups for the active company",
        company_param="company",
    )

    endpoint(
        g,
        "users",
        path="/api/auth/getallusers",
        help="User directory (id, name, phone, email, role, status)",
        company_param="company",
    )

    # -- Shared layout permission rows (capability discovery) -------------
    endpoint(
        g,
        "permissions",
        path="/api/Permission/GetUserEffectivePermissions",
        help="Module/permission rows for a user under the active company",
        params=[
            {
                "name": "UserId",
                "type": int,
                "positional": True,
                "required": False,
                "default": CONFIG.user_id,
                "help": f"User id (default {CONFIG.user_id})",
            }
        ],
        company_param="CompanyId",
    )
